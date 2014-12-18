package de.zalando.zmon.service.impl;

import java.io.IOException;

import java.util.Collection;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.ObjectMapper;

import com.google.common.base.Preconditions;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;

import de.zalando.eventlog.EventLogger;

import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.domain.DowntimeDetails;
import de.zalando.zmon.domain.DowntimeEntities;
import de.zalando.zmon.domain.DowntimeRequest;
import de.zalando.zmon.event.ZMonEventType;
import de.zalando.zmon.exception.SerializationException;
import de.zalando.zmon.persistence.AlertDefinitionSProcService;
import de.zalando.zmon.redis.RedisPattern;
import de.zalando.zmon.redis.ResponseHolder;
import de.zalando.zmon.rest.DowntimeGroup;
import de.zalando.zmon.service.DowntimeService;
import de.zalando.zmon.util.Numbers;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.Pipeline;
import redis.clients.jedis.Response;

@Service
public class DowntimeServiceImpl implements DowntimeService {

    private static final Logger LOG = LoggerFactory.getLogger(DowntimeServiceImpl.class);

    private static final EventLogger EVENT_LOG = EventLogger.getLogger(DowntimeServiceImpl.class);

    private final JedisPool redisPool;
    private final ObjectMapper mapper;
    private final AlertDefinitionSProcService alertDefinintionSProc;

    @Autowired
    public DowntimeServiceImpl(final JedisPool redisPool, final ObjectMapper mapper,
            final AlertDefinitionSProcService alertDefinintionSProc) {
        this.redisPool = Preconditions.checkNotNull(redisPool, "redisPool");
        this.mapper = Preconditions.checkNotNull(mapper, "mapper");
        this.alertDefinintionSProc = Preconditions.checkNotNull(alertDefinintionSProc, "alertDefinintionSProc");
    }

    @Override
    public DowntimeGroup scheduleDowntimeGroup(final DowntimeGroup group) {
        // well, not performant, but at least we don't need to touch python

        // load all active alert ids
        final Set<Integer> ids = group.getAlertDefinitions() == null
            ? ImmutableSet.copyOf(alertDefinintionSProc.getAlertIdsByStatus(DefinitionStatus.ACTIVE))
            : group.getAlertDefinitions();

        final Map<Integer, Response<Set<String>>> results = resolveEntities(ids);

        // filter entities
        final Set<Integer> alertDefinitionsInDowntime = new HashSet<>(results.size());
        final Set<String> entitiesInDowntime = new HashSet<>();
        final List<DowntimeEntities> requests = new LinkedList<>();
        for (final Map.Entry<Integer, Response<Set<String>>> entry : results.entrySet()) {
            final Set<String> entities = Sets.intersection(group.getEntities(), entry.getValue().get());
            if (!entities.isEmpty()) {
                alertDefinitionsInDowntime.add(entry.getKey());
                entitiesInDowntime.addAll(entities);

                final DowntimeEntities downtimeEntities = new DowntimeEntities();
                downtimeEntities.setAlertDefinitionId(entry.getKey());
                downtimeEntities.setEntityIds(entities);
                requests.add(downtimeEntities);
            }
        }

        final String groupId = UUID.randomUUID().toString();
        doScheduleDowntime(group, groupId, requests);

        final DowntimeGroup response = new DowntimeGroup();
        response.setId(groupId);
        response.setStartTime(group.getStartTime());
        response.setEndTime(group.getEndTime());
        response.setComment(group.getComment());
        response.setCreatedBy(group.getCreatedBy());
        response.setAlertDefinitions(alertDefinitionsInDowntime);
        response.setEntities(entitiesInDowntime);

        return response;
    }

    private Map<Integer, Response<Set<String>>> resolveEntities(final Collection<Integer> ids) {
        final Map<Integer, Response<Set<String>>> results = Maps.newHashMapWithExpectedSize(ids.size());
        final Jedis jedis = redisPool.getResource();
        try {
            final Pipeline pipeline = jedis.pipelined();
            for (final Integer id : ids) {
                results.put(id, pipeline.hkeys(RedisPattern.alertFilterEntities(id)));
            }

            pipeline.sync();
        } finally {
            redisPool.returnResource(jedis);
        }

        return results;
    }

    private void doScheduleDowntime(final DowntimeGroup group, final String groupId,
            final List<DowntimeEntities> requests) {
        if (!requests.isEmpty()) {
            final DowntimeRequest request = new DowntimeRequest();
            request.setDowntimeEntities(requests);
            request.setEndTime(group.getEndTime());
            request.setComment(group.getComment());
            request.setCreatedBy(group.getCreatedBy());
            request.setStartTime(group.getStartTime());

            scheduleDowntime(request, groupId);
        }
    }

    @Override
    public List<String> scheduleDowntime(final DowntimeRequest request) {
        return scheduleDowntime(request, UUID.randomUUID().toString());
    }

    private List<String> scheduleDowntime(final DowntimeRequest request, final String groupId) {
        Preconditions.checkNotNull(request, "request");
        Preconditions.checkNotNull(groupId, "groupId");

        final List<String> downtimeIds = new LinkedList<>();
        final Collection<DowntimeDetails> newDowntimes = new LinkedList<>();

        final Jedis jedis = redisPool.getResource();
        try {

            // create pipeline
            final Pipeline p = jedis.pipelined();
            for (final DowntimeEntities downtimeEntities : request.getDowntimeEntities()) {
                p.sadd(RedisPattern.downtimeAlertIds(), String.valueOf(downtimeEntities.getAlertDefinitionId()));

                final String entitiesPattern = RedisPattern.downtimeEntities(downtimeEntities.getAlertDefinitionId());
                for (final String entity : downtimeEntities.getEntityIds()) {
                    p.sadd(entitiesPattern, entity);

                    // generate id
                    final String id = UUID.randomUUID().toString();

                    final DowntimeDetails details = new DowntimeDetails();
                    details.setId(id);
                    details.setGroupId(groupId);
                    details.setComment(request.getComment());
                    details.setStartTime(request.getStartTime());
                    details.setEndTime(request.getEndTime());
                    details.setAlertDefinitionId(downtimeEntities.getAlertDefinitionId());
                    details.setEntity(entity);
                    details.setCreatedBy(request.getCreatedBy());

                    try {
                        final String json = mapper.writeValueAsString(details);
                        p.hset(RedisPattern.downtimeDetails(downtimeEntities.getAlertDefinitionId(), entity), id, json);
                        p.hset(RedisPattern.downtimeScheduleQueue(), id, json);
                        p.publish(RedisPattern.downtimeScheduleChannel(), id);
                        newDowntimes.add(details);
                    } catch (final IOException e) {
                        throw new SerializationException("Could not write JSON: " + details, e);
                    }

                    downtimeIds.add(id);
                }
            }

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }

        // only log events at the end of the transaction
        for (final DowntimeDetails details : newDowntimes) {
            EVENT_LOG.log(ZMonEventType.DOWNTIME_SCHEDULED, details.getAlertDefinitionId(), details.getEntity(),
                details.getStartTime(), details.getEndTime(), details.getCreatedBy(), details.getComment());
        }

        return downtimeIds;
    }

    @Override
    public List<DowntimeDetails> getDowntimes(final Set<Integer> alertDefinitionIds) {

        final List<Response<Map<String, String>>> asyncDowntimeResults = new LinkedList<>();

        // only process results after returning the connection to the pool
        // we should hold the connection as less time as possible since we have a limited number of connections
        final Jedis jedis = redisPool.getResource();

        try {
            final Set<Integer> alertIdsWithDowntime = Sets.intersection(alertDefinitionIds, alertsInDowntime(jedis));
            if (!alertIdsWithDowntime.isEmpty()) {
                final List<ResponseHolder<Integer, Set<String>>> asyncAlertResults = fetchEntities(jedis,
                        alertIdsWithDowntime);

                // execute async call to get all downtime data for each entity
                final Pipeline p = jedis.pipelined();
                for (final ResponseHolder<Integer, Set<String>> response : asyncAlertResults) {
                    for (final String entity : response.getResponse().get()) {
                        asyncDowntimeResults.add(p.hgetAll(RedisPattern.downtimeDetails(response.getKey(), entity)));
                    }
                }

                p.sync();
            }
        } finally {
            redisPool.returnResource(jedis);
        }

        // process results
        return processDowntimeResponses(asyncDowntimeResults);
    }

    private List<DowntimeDetails> processDowntimeResponses(final List<Response<Map<String, String>>> downtimeResults) {

        final List<DowntimeDetails> results = new LinkedList<>();
        for (final Response<Map<String, String>> response : downtimeResults) {
            for (final String entityResults : response.get().values()) {
                try {
                    results.add(mapper.readValue(entityResults, DowntimeDetails.class));
                } catch (final IOException e) {
                    throw new SerializationException("Could not read JSON: " + entityResults, e);
                }
            }
        }

        return results;
    }

    @Override
    public DowntimeGroup deleteDowntimeGroup(final String groupId) {
        Preconditions.checkNotNull(groupId, "groupId");

        final Collection<Response<List<String>>> deleteResults = new LinkedList<>();
        final Jedis jedis = redisPool.getResource();
        try {
            final List<ResponseHolder<Integer, Set<String>>> asyncAlertEntities = fetchEntities(jedis,
                    alertsInDowntime(jedis));

            // this is slow but we are not expecting so many deletes
            final Pipeline p = jedis.pipelined();
            for (final ResponseHolder<Integer, Set<String>> response : asyncAlertEntities) {
                for (final String entity : response.getResponse().get()) {
                    deleteResults.add(p.hvals(RedisPattern.downtimeDetails(response.getKey(), entity)));
                }
            }

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }

        final Map<String, DowntimeDetailsFormat> toRemoveJsonDetails = Maps.newHashMapWithExpectedSize(
                deleteResults.size());
        for (final Response<List<String>> response : deleteResults) {
            for (final String jsonDetails : response.get()) {
                try {
                    final DowntimeDetails details = mapper.readValue(jsonDetails, DowntimeDetails.class);
                    if (groupId.equals(details.getGroupId())) {
                        toRemoveJsonDetails.put(details.getId(), new DowntimeDetailsFormat(details, jsonDetails));
                    }
                } catch (final IOException e) {
                    throw new SerializationException("Could not read JSON: " + jsonDetails, e);
                }
            }
        }

        final List<DowntimeDetails> deletedDowntimes = processDeleteDowntimes(toRemoveJsonDetails);
        final DowntimeGroup response = new DowntimeGroup();
        response.setId(groupId);
        response.setAlertDefinitions(new HashSet<Integer>());
        response.setEntities(new HashSet<String>());

        final Iterator<DowntimeDetails> iterator = deletedDowntimes.iterator();
        if (iterator.hasNext()) {
            final DowntimeDetails details = iterator.next();
            response.setComment(details.getComment());
            response.setStartTime(details.getStartTime());
            response.setEndTime(details.getEndTime());
            response.setCreatedBy(details.getCreatedBy());
            response.getEntities().add(details.getEntity());
            response.getAlertDefinitions().add(details.getAlertDefinitionId());
        }

        while (iterator.hasNext()) {
            final DowntimeDetails details = iterator.next();
            response.getEntities().add(details.getEntity());
            response.getAlertDefinitions().add(details.getAlertDefinitionId());
        }

        return response;
    }

    @Override
    public void deleteDowntimes(final Set<String> downtimeIds) {
        Preconditions.checkNotNull(downtimeIds);

        if (!downtimeIds.isEmpty()) {
            final Collection<Response<String>> deleteResults = new LinkedList<>();

            final Jedis jedis = redisPool.getResource();
            try {
                final List<ResponseHolder<Integer, Set<String>>> asyncAlertEntities = fetchEntities(jedis,
                        alertsInDowntime(jedis));

                // this is slow but we are not expecting so many deletes
                final Pipeline p = jedis.pipelined();
                for (final ResponseHolder<Integer, Set<String>> response : asyncAlertEntities) {
                    for (final String entity : response.getResponse().get()) {
                        for (final String downtimeId : downtimeIds) {
                            deleteResults.add(p.hget(RedisPattern.downtimeDetails(response.getKey(), entity),
                                    downtimeId));
                        }
                    }
                }

                p.sync();
            } finally {
                redisPool.returnResource(jedis);
            }

            final Map<String, DowntimeDetailsFormat> toRemoveJsonDetails = Maps.newHashMapWithExpectedSize(
                    deleteResults.size());
            for (final Response<String> response : deleteResults) {
                final String jsonDetails = response.get();
                if (jsonDetails != null) {
                    try {
                        final DowntimeDetails details = mapper.readValue(jsonDetails, DowntimeDetails.class);
                        toRemoveJsonDetails.put(details.getId(), new DowntimeDetailsFormat(details, jsonDetails));
                    } catch (final IOException e) {
                        throw new SerializationException("Could not read JSON: " + jsonDetails, e);
                    }
                }
            }

            // check if the downtime was deleted
            processDeleteDowntimes(toRemoveJsonDetails);
        }
    }

    private List<ResponseHolder<Integer, Set<String>>> fetchEntities(final Jedis jedis,
            final Iterable<Integer> alertIdsWithDowntime) {
        final List<ResponseHolder<Integer, Set<String>>> asyncAlertEntities = new LinkedList<>();

        final Pipeline p = jedis.pipelined();
        for (final Integer alertDefinitionId : alertIdsWithDowntime) {
            asyncAlertEntities.add(ResponseHolder.create(alertDefinitionId,
                    p.smembers(RedisPattern.downtimeEntities(alertDefinitionId))));
        }

        p.sync();

        return asyncAlertEntities;
    }

    private ImmutableSet<Integer> alertsInDowntime(final Jedis jedis) {
        return FluentIterable.from(jedis.smembers(RedisPattern.downtimeAlertIds()))
                             .transform(Numbers.PARSE_INTEGER_FUNCTION).toSet();
    }

    private List<DowntimeDetails> processDeleteDowntimes(final Map<String, DowntimeDetailsFormat> toRemove) {

        // extract downtimes to delete
        final List<DowntimeDetails> deleted = new LinkedList<>();
        final List<ResponseHolder<String, Long>> asyncResponses = new LinkedList<>();

        // execute delete
        if (!toRemove.isEmpty()) {
            final Jedis jedis = redisPool.getResource();
            try {
                Pipeline p = jedis.pipelined();
                for (final DowntimeDetailsFormat details : toRemove.values()) {
                    asyncResponses.add(ResponseHolder.create(details.getDowntimeDetails().getId(),
                            p.hdel(
                                RedisPattern.downtimeDetails(details.getDowntimeDetails().getAlertDefinitionId(),
                                    details.getDowntimeDetails().getEntity()), details.getDowntimeDetails().getId())));
                }

                p.sync();

                // check which entries were deleted and publish an event
                p = jedis.pipelined();
                for (final ResponseHolder<String, Long> response : asyncResponses) {
                    if (response.getResponse().get() > 0) {
                        final DowntimeDetailsFormat value = toRemove.get(response.getKey());
                        p.hset(RedisPattern.downtimeRemoveQueue(), response.getKey(), value.getJson());
                        p.publish(RedisPattern.downtimeRemoveChannel(), response.getKey());
                        deleted.add(value.getDowntimeDetails());
                    }
                }

                p.sync();
            } finally {
                redisPool.returnResource(jedis);
            }

            // and finnally publish an event after returning the connection
            for (final DowntimeDetails details : deleted) {
                EVENT_LOG.log(ZMonEventType.DOWNTIME_REMOVED, details.getAlertDefinitionId(), details.getEntity(),
                    details.getStartTime(), details.getEndTime(), details.getCreatedBy(), details.getComment());
            }

        }

        return deleted;
    }

    private static final class DowntimeDetailsFormat {
        private final DowntimeDetails downtimeDetails;
        private final String json;

        private DowntimeDetailsFormat(final DowntimeDetails downtimeDetails, final String json) {
            this.downtimeDetails = downtimeDetails;
            this.json = json;
        }

        public DowntimeDetails getDowntimeDetails() {
            return downtimeDetails;
        }

        public String getJson() {
            return json;
        }
    }
}
