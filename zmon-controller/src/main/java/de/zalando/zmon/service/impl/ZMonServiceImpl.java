package de.zalando.zmon.service.impl;

import java.io.IOException;

import java.util.*;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import com.google.common.base.Preconditions;
import com.google.common.collect.HashMultimap;
import com.google.common.collect.SetMultimap;

import de.zalando.eventlog.EventLogger;

import de.zalando.zmon.diff.CheckDefinitionsDiffFactory;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.CheckDefinition;
import de.zalando.zmon.domain.CheckDefinitionImport;
import de.zalando.zmon.domain.CheckDefinitions;
import de.zalando.zmon.domain.CheckDefinitionsDiff;
import de.zalando.zmon.domain.CheckResults;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.domain.ExecutionStatus;
import de.zalando.zmon.domain.WorkerQueue;
import de.zalando.zmon.event.ZMonEventType;
import de.zalando.zmon.exception.SerializationException;
import de.zalando.zmon.persistence.AlertDefinitionSProcService;
import de.zalando.zmon.persistence.CheckDefinitionImportResult;
import de.zalando.zmon.persistence.CheckDefinitionSProcService;
import de.zalando.zmon.persistence.ZMonSProcService;
import de.zalando.zmon.redis.RedisPattern;
import de.zalando.zmon.redis.ResponseHolder;
import de.zalando.zmon.service.ZMonService;
import de.zalando.zmon.util.DBUtil;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.Pipeline;
import redis.clients.jedis.Response;

// TODO remove CheckDefinitionImport and use CheckDefinition with optional id
// TODO convert mandatory types into native types (Integer -> int...)
// TODO key class to hide key details
// TODO handle exceptions carefully
// TODO check if WSDL is in sync with methods
// TODO abstract diff logic (reuse code)
// TODO use the latest version of SP and optionals
// TODO the latest version of zomcat and expose statistics
// TODO remove autowire and use DI properly
// TODO use history tables instead of timestamp as a snapshot to get more accurate results
// TODO check security and command encoding
// TODO add documentation
// TODO configure ObjectMapperFactoryBean to always convert date to seconds
// TODO rename service to CheckServiceImpl
// TODO move security validation logic to service. Move has*Permission from authority to other service and build a
// compositePermissionManager

@Service("zmon-redis-service")
public class ZMonServiceImpl implements ZMonService {

    private static final EventLogger EVENT_LOG = EventLogger.getLogger(ZMonServiceImpl.class);

    private static final Logger LOG = LoggerFactory.getLogger(ZMonServiceImpl.class);

    private static final long MAX_ACTIVE_WORKER_TIMESTAMP_MILLIS_AGO = 24 * 1000;

    @Autowired
    protected CheckDefinitionSProcService checkDefinitionSProc;

    @Autowired
    protected AlertDefinitionSProcService alertDefinitionSProc;

    @Autowired
    protected ZMonSProcService zmonSProc;

    @Autowired
    protected JedisPool redisPool;

    @Autowired
    protected ObjectMapper mapper;

    @Override
    public ExecutionStatus getStatus() {

        final Map<String, Response<Long>> queueSize = new HashMap<>();
        final Map<String, Response<String>> lastUpdate = new HashMap<>();
        final Map<String, Response<String>> invocations = new HashMap<>();

        final Jedis jedis = redisPool.getResource();
        try {
            final Set<String> workerNames = jedis.smembers(RedisPattern.workerNames());

            final Pipeline p = jedis.pipelined();

            for (final WorkerQueue queue : WorkerQueue.values()) {
                queueSize.put(queue.getKey(), p.llen(queue.getKey()));
            }

            for (final String worker : workerNames) {
                lastUpdate.put(worker, p.get(RedisPattern.workerLastUpdated(worker)));
                invocations.put(worker, p.get(RedisPattern.workerCheckInvocations(worker)));
            }

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }

        return buildStatus(queueSize, lastUpdate, invocations);
    }

    private ExecutionStatus buildStatus(final Map<String, Response<Long>> queueSize,
            final Map<String, Response<String>> lastUpdates, final Map<String, Response<String>> invocations) {

        final ExecutionStatus.Builder builder = ExecutionStatus.builder();

        // add queue info
        for (final Map.Entry<String, Response<Long>> size : queueSize.entrySet()) {
            builder.addQueue(size.getKey(), size.getValue().get());
        }

        // worker info
        int workersActive = 0;
        for (final Map.Entry<String, Response<String>> lastUpdate : lastUpdates.entrySet()) {
            final String val = lastUpdate.getValue().get();
            double ts = 0;
            if (val != null) {
                ts = Double.valueOf(val);

                // "ts" is stored as seconds, but in Java we have Milliseconds
                if ((long) (ts * 1000) > System.currentTimeMillis() - MAX_ACTIVE_WORKER_TIMESTAMP_MILLIS_AGO) {
                    workersActive++;
                }
            }

            final String invocation = invocations.get(lastUpdate.getKey()).get();
            builder.addWorker(lastUpdate.getKey(), (long) ts, invocation == null ? 0 : Long.valueOf(invocation));
        }

        builder.withWorkersActive(workersActive);

        return builder.build();
    }

    @Override
    public List<String> getAllTeams() {
        final List<String> teams = zmonSProc.getAllTeams();
        Collections.sort(teams);

        return teams;
    }

    @Override
    public List<CheckDefinition> getCheckDefinitions(final DefinitionStatus status,
            final List<Integer> checkDefinitionIds) {
        return checkDefinitionSProc.getCheckDefinitions(status, checkDefinitionIds);
    }

    @Override
    public List<CheckDefinition> getCheckDefinitions(final DefinitionStatus status, final Set<String> teams) {
        Preconditions.checkNotNull(teams, "teams");

        // SP doesn't support sets
        final List<String> teamList = new ArrayList<>(teams.size());
        for (final String team : teams) {
            teamList.add(DBUtil.prefix(team));
        }

        return checkDefinitionSProc.getCheckDefinitionsByOwningTeam(status, teamList);
    }

    @Override
    public CheckDefinitions getCheckDefinitions(final DefinitionStatus status) {
        return checkDefinitionSProc.getAllCheckDefinitions(status);
    }

    @Override
    public CheckDefinitionsDiff getCheckDefinitionsDiff(final Long snapshotId) {
        return CheckDefinitionsDiffFactory.create(checkDefinitionSProc.getCheckDefinitionsDiff(snapshotId));

    }

    @Override
    public CheckDefinition createOrUpdateCheckDefinition(final CheckDefinitionImport checkDefinition) {
        Preconditions.checkNotNull(checkDefinition);
        LOG.info("Saving check definition '{}' from team '{}'", checkDefinition.getName(),
            checkDefinition.getOwningTeam());

        final CheckDefinitionImportResult operationResult = checkDefinitionSProc.createOrUpdateCheckDefinition(
                checkDefinition);
        final CheckDefinition result = operationResult.getEntity();

        EVENT_LOG.log(operationResult.isNewEntity() ? ZMonEventType.CHECK_DEFINITION_CREATED
                                                    : ZMonEventType.CHECK_DEFINITION_UPDATED, result.getId(),
            result.getEntities(), result.getCommand(), result.getLastModifiedBy());

        return result;
    }

    @Override
    public void deleteCheckDefinition(final String userName, final String name, final String owningTeam) {
        Preconditions.checkNotNull(userName);
        Preconditions.checkNotNull(name);
        Preconditions.checkNotNull(owningTeam);

        LOG.info("Deleting check definition with name {} and team {}", name, owningTeam);

        final CheckDefinition checkDefinition = checkDefinitionSProc.deleteCheckDefinition(userName, name, owningTeam);

        if (checkDefinition != null) {
            EVENT_LOG.log(ZMonEventType.CHECK_DEFINITION_DELETED, checkDefinition.getId(),
                checkDefinition.getEntities(), checkDefinition.getCommand(), userName);
        }
    }

    @Override
    public void deleteDetachedCheckDefinitions() {
        LOG.info("Deleting detached check definitions");

        List<Integer> checkIds = Collections.emptyList();
        final List<CheckDefinition> deletedChecks = checkDefinitionSProc.deleteDetachedCheckDefinitions();
        if (deletedChecks != null && !deletedChecks.isEmpty()) {
            checkIds = new LinkedList<>();
            for (final CheckDefinition checkDefinition : deletedChecks) {
                checkIds.add(checkDefinition.getId());
            }
        }

        LOG.info("Detached check definitions: {}", checkIds);
    }

    @Override
    public List<CheckResults> getCheckResults(final int checkId, final String entity, final int limit) {
        final List<ResponseHolder<String, List<String>>> results = new LinkedList<>();
        final List<ResponseHolder<Integer, Set<String>>> alertEntities = new LinkedList<>();

        final List<Integer> alertDefinitionIds = alertDefinitionSProc.getAlertIdsByCheckId(checkId);
        final Jedis jedis = redisPool.getResource();
        try {
            final Set<String> entities = (entity == null ? jedis.smembers(RedisPattern.checkEntities(checkId))
                                                         : Collections.singleton(entity));
            if (!entities.isEmpty()) {

                // execute async calls
                final Pipeline p = jedis.pipelined();
                for (final String key : entities) {
                    results.add(ResponseHolder.create(key,
                            p.lrange(RedisPattern.checkResult(checkId, key), 0, limit - 1)));
                }

                for (final Integer alertDefinitionId : alertDefinitionIds) {
                    alertEntities.add(ResponseHolder.create(alertDefinitionId,
                            p.smembers(RedisPattern.alertEntities(alertDefinitionId))));
                }

                p.sync();
            }
        } finally {
            redisPool.returnResource(jedis);
        }

        final List<CheckResults> checkResults = buildCheckResults(results);

        // group all ids by entity
        final SetMultimap<String, Integer> entities = HashMultimap.create();
        for (final ResponseHolder<Integer, Set<String>> response : alertEntities) {
            for (final String alertEntity : response.getResponse().get()) {
                entities.put(alertEntity, response.getKey());
            }
        }

        for (final CheckResults checkResult : checkResults) {
            checkResult.setActiveAlertIds(entities.get(checkResult.getEntity()));
        }

        return checkResults;
    }

    @Override
    public List<CheckResults> getCheckAlertResults(final int alertId, final int limit) {

        // get alert definitions from database
        final List<AlertDefinition> definitions = alertDefinitionSProc.getAlertDefinitions(DefinitionStatus.ACTIVE,
                Collections.singletonList(alertId));

        List<CheckResults> checkResults = Collections.emptyList();

        if (!definitions.isEmpty()) {

            // TODO create sproc getAlertDefinition
            final AlertDefinition alertDefinition = definitions.get(0);

            final List<ResponseHolder<String, List<String>>> results = new LinkedList<>();

            final Jedis jedis = redisPool.getResource();
            final Map<String, String> entities;
            try {
                entities = jedis.hgetAll(RedisPattern.alertFilterEntities(alertId));
                if (!entities.isEmpty()) {

                    // execute an async calls
                    final Pipeline p = jedis.pipelined();
                    for (final String key : entities.keySet()) {
                        results.add(ResponseHolder.create(key,
                                p.lrange(RedisPattern.checkResult(alertDefinition.getCheckDefinitionId(), key), 0,
                                    limit - 1)));
                    }

                    p.sync();
                }
            } finally {
                redisPool.returnResource(jedis);
            }

            checkResults = buildCheckResults(results);

            final Set<Integer> activeAlertIds = Collections.singleton(alertId);
            for (final CheckResults cr : checkResults) {
                cr.setActiveAlertIds(activeAlertIds);
                try {
                    final JsonNode captures = mapper.readTree(entities.get(cr.getEntity()));
                    for (final JsonNode node : cr.getResults()) {
                        ((ObjectNode) node).put("captures", captures);
                    }
                } catch (final IOException e) {
                    throw new SerializationException("Could not read capture's JSON: " + entities.get(cr.getEntity()),
                        e);
                }
            }
        }

        return checkResults;
    }

    @Override
    public JsonNode getEntityProperties() {
        final String json = getEntityPropertiesFromRedis();
        try {
            return mapper.readTree(json);
        } catch (final IOException e) {
            throw new SerializationException("Could not read JSON: " + json, e);
        }
    }

    private String getEntityPropertiesFromRedis() {
        final Jedis jedis = redisPool.getResource();
        try {
            return jedis.get(RedisPattern.entityProperties());
        } finally {
            redisPool.returnResource(jedis);
        }
    }

    private List<CheckResults> buildCheckResults(final List<ResponseHolder<String, List<String>>> results) {

        final List<CheckResults> checkResults = new LinkedList<>();

        // process checks
        for (final ResponseHolder<String, List<String>> entry : results) {
            final List<String> entityResults = entry.getResponse().get();

            if (!entityResults.isEmpty()) {
                final CheckResults result = new CheckResults();
                result.setEntity(entry.getKey());

                final List<JsonNode> jsonResult = new LinkedList<>();
                for (final String json : entityResults) {
                    try {
                        jsonResult.add(mapper.readTree(json));
                    } catch (final IOException e) {
                        throw new SerializationException("Could not read JSON: " + json, e);
                    }
                }

                result.setResults(jsonResult);
                checkResults.add(result);
            }
        }

        return checkResults;
    }

}
