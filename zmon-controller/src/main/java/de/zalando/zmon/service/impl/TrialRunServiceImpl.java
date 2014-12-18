package de.zalando.zmon.service.impl;

import java.io.IOException;

import java.util.LinkedList;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import com.google.common.base.Preconditions;

import de.zalando.eventlog.EventLogger;

import de.zalando.zmon.domain.TrialRunRequest;
import de.zalando.zmon.domain.TrialRunResults;
import de.zalando.zmon.event.ZMonEventType;
import de.zalando.zmon.exception.SerializationException;
import de.zalando.zmon.redis.RedisPattern;
import de.zalando.zmon.service.TrialRunService;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.Pipeline;
import redis.clients.jedis.Response;

@Service
public class TrialRunServiceImpl implements TrialRunService {

    private static final EventLogger EVENT_LOG = EventLogger.getLogger(TrialRunServiceImpl.class);

    // expiration time in seconds
    private static final int TRIAL_RUN_EXPIRATION_TIME = 300;

    @Autowired
    private JedisPool redisPool;

    @Autowired
    private ObjectMapper mapper;

    @Override
    public String scheduleTrialRun(final TrialRunRequest request) {
        Preconditions.checkNotNull(request, "request");

        final String id = UUID.randomUUID().toString();
        request.setId(id);

        try {
            final String json = mapper.writeValueAsString(request);

            final Jedis jedis = redisPool.getResource();
            try {
                final Pipeline p = jedis.pipelined();

                p.hset(RedisPattern.trialRunQueue(), id, json);

                // expire queue. The scheduler might be down
                p.expire(RedisPattern.trialRunQueue(), TRIAL_RUN_EXPIRATION_TIME);

                p.publish(RedisPattern.trialRunChannel(), id);

                p.sync();

            } finally {
                redisPool.returnResource(jedis);
            }

        } catch (final IOException e) {
            throw new SerializationException("Could not write JSON: " + request, e);
        }

        EVENT_LOG.log(ZMonEventType.TRIAL_RUN_SCHEDULED, request.getCheckCommand(), request.getAlertCondition(),
            request.getEntities(), request.getPeriod(), request.getCreatedBy());

        return id;
    }

    @Override
    public TrialRunResults getTrialRunResults(final String id) {
        Preconditions.checkNotNull(id);

        final String entitiesKey = RedisPattern.trialRunEntities(id);

        Response<Boolean> keyExists;
        Response<Set<String>> entitiesResponse;
        Response<Map<String, String>> resultsResponse;

        final Jedis jedis = redisPool.getResource();
        try {
            final Pipeline p = jedis.pipelined();

            keyExists = p.hexists(RedisPattern.trialRunQueue(), id);
            entitiesResponse = p.smembers(entitiesKey);
            resultsResponse = p.hgetAll(RedisPattern.trialRunResults(id));

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }

        return processTrialRunResponses(keyExists, entitiesResponse, resultsResponse);
    }

    private TrialRunResults processTrialRunResponses(final Response<Boolean> keyExists,
            final Response<Set<String>> entitiesResponse, final Response<Map<String, String>> resultsResponse) {

        final Set<String> entities = entitiesResponse.get();
        final Map<String, String> results = resultsResponse.get();

        final TrialRunResults trialResults = new TrialRunResults();
        trialResults.setPercentage(keyExists.get()
                ? 0 : entities.isEmpty() ? 100 : (int) ((float) results.size() / (float) entities.size() * 100));

        final LinkedList<JsonNode> jsonResults = new LinkedList<>();
        trialResults.setResults(jsonResults);

        for (final Map.Entry<String, String> result : results.entrySet()) {
            try {
                jsonResults.add(mapper.readValue(result.getValue(), JsonNode.class));
            } catch (final IOException e) {
                throw new SerializationException("Could not read JSON: " + result, e);
            }
        }

        return trialResults;
    }

}
