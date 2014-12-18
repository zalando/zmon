package de.zalando.zmon.service.impl;

import java.io.IOException;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.UUID;

import javax.annotation.Nullable;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import com.google.common.base.Function;
import com.google.common.base.Preconditions;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;

import de.zalando.eventlog.EventLogger;

import de.zalando.zmon.diff.AlertDefinitionsDiffFactory;
import de.zalando.zmon.domain.Alert;
import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.AlertDefinitionAuth;
import de.zalando.zmon.domain.AlertDefinitions;
import de.zalando.zmon.domain.AlertDefinitionsDiff;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.domain.LastCheckResult;
import de.zalando.zmon.event.ZMonEventType;
import de.zalando.zmon.exception.SerializationException;
import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.persistence.AlertDefinitionOperationResult;
import de.zalando.zmon.persistence.AlertDefinitionSProcService;
import de.zalando.zmon.redis.RedisPattern;
import de.zalando.zmon.redis.ResponseHolder;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.AlertService;
import de.zalando.zmon.util.DBUtil;
import de.zalando.zmon.util.NamedMessageFormatter;
import de.zalando.zmon.util.Numbers;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.Pipeline;

// TODO diffs should never return null collections. They should be empty instead
@Service("alert-service-redis")
public class AlertServiceImpl implements AlertService {

    private static final Logger LOG = LoggerFactory.getLogger(AlertServiceImpl.class);

    private static final EventLogger EVENT_LOG = EventLogger.getLogger(AlertServiceImpl.class);

    private static final String ENTITIES_PLACEHOLDER = "entities";
    private static final String CAPTURES_KEY = "captures";
    private static final String DOWNTIMES_KEY = "downtimes";

    // expiration time in seconds
    private static final int INSTANTANEOUS_ALERT_EVALUATION_TIME = 300;

    private final NamedMessageFormatter messageFormatter = new NamedMessageFormatter();

    private final Function<AlertDefinition, Integer> uniqueAlertDefinitionFunction =
        new Function<AlertDefinition, Integer>() {

            @Override
            public Integer apply(final AlertDefinition input) {
                return input.getId();
            }
        };

    @Autowired
    protected AlertDefinitionSProcService alertDefinintionSProc;

    @Autowired
    protected ZMonAuthorityService authorityService;

    @Autowired
    private JedisPool redisPool;

    @Autowired
    private ObjectMapper mapper;

    @Override
    public AlertDefinition createOrUpdateAlertDefinition(final AlertDefinition alertDefinition) throws ZMonException {
        Preconditions.checkNotNull(alertDefinition);

        final AlertDefinitionOperationResult operationResult = alertDefinintionSProc.createOrUpdateAlertDefinitionTree(
                alertDefinition).throwExceptionOnFailure();
        final AlertDefinition result = operationResult.getEntity();

        // TODO save inherited data to eventlog, or the diff?
        EVENT_LOG.log(alertDefinition.getId() == null ? ZMonEventType.ALERT_DEFINITION_CREATED
                                                      : ZMonEventType.ALERT_DEFINITION_UPDATED, result.getId(),
            result.getEntities(), result.getCondition(), result.getLastModifiedBy());

        return result;
    }

    @Override
    public AlertDefinition deleteAlertDefinition(final int id) throws ZMonException {
        LOG.info("Deleting alert definition with id '{}'", id);

        final AlertDefinitionOperationResult operationResult = alertDefinintionSProc.deleteAlertDefinition(id)
                                                                                    .throwExceptionOnFailure();
        final AlertDefinition alertDefinition = operationResult.getEntity();

        if (alertDefinition != null) {
            EVENT_LOG.log(ZMonEventType.ALERT_DEFINITION_DELETED, alertDefinition.getId(),
                alertDefinition.getEntities(), alertDefinition.getCondition(), authorityService.getUserName());
        }

        return alertDefinition;
    }

    @Override
    public List<AlertDefinition> getAllAlertDefinitions() {
        return alertDefinintionSProc.getAllAlertDefinitions();
    }

    @Override
    public AlertDefinitions getActiveAlertDefinitionsDiff() {
        return alertDefinintionSProc.getActiveAlertDefinitionsDiff();
    }

    @Override
    public AlertDefinitionsDiff getAlertDefinitionsDiff(final Long snapshotId) {
        return AlertDefinitionsDiffFactory.create(alertDefinintionSProc.getAlertDefinitionsDiff(snapshotId));
    }

    @Override
    public List<AlertDefinition> getAlertDefinitions(final DefinitionStatus status,
            final List<Integer> alertDefinitionIds) {
        Preconditions.checkNotNull(alertDefinitionIds, "alertDefinitionIds");

        return alertDefinintionSProc.getAlertDefinitions(status, alertDefinitionIds);
    }

    @Override
    public List<AlertDefinition> getAlertDefinitions(@Nullable final DefinitionStatus status, final Set<String> teams) {
        Preconditions.checkNotNull(teams, "teams");

        // SP doesn't support sets
        final List<String> teamList = new ArrayList<>(teams.size());
        for (final String team : teams) {
            teamList.add(DBUtil.prefix(team));
        }

        return alertDefinintionSProc.getAlertDefinitionsByTeam(status, teamList);
    }

    @Override
    public List<Alert> getAllAlerts() {
        return fetchAlertsById(FluentIterable.from(getActiveAlertIds()).transform(Numbers.PARSE_INTEGER_FUNCTION)
                    .toSet());
    }

    @Override
    public List<Alert> getAllAlertsById(final Set<Integer> alertIdfilter) {
        Preconditions.checkNotNull(alertIdfilter, "alertIdfilter");

        List<Alert> alerts = Collections.emptyList();

        if (!alertIdfilter.isEmpty()) {

            // first extract the id of all active alerts
            final Set<String> redisAlertIds = getActiveAlertIds();

            // apply the filter
            final Set<Integer> alertIds = Sets.newHashSetWithExpectedSize(redisAlertIds.size());
            for (final String alertId : redisAlertIds) {
                final Integer alertIdValue = Integer.valueOf(alertId);
                if (alertIdfilter.contains(alertIdValue)) {
                    alertIds.add(alertIdValue);
                }
            }

            alerts = fetchAlertsById(alertIds);
        }

        return alerts;
    }

    protected Set<String> getActiveAlertIds() {
        final Jedis jedis = redisPool.getResource();
        try {
            return jedis.smembers(RedisPattern.alertIds());
        } finally {
            redisPool.returnResource(jedis);
        }
    }

    protected void getAlertDataFromStorage(Set<Integer> ids, List<Integer> alertIds, List<ResponseHolder<Integer,Set<String>>> results) {
        // first extract everything and return the connection to the connection pool
        final Jedis jedis = redisPool.getResource();
        try {

            // execute async call
            final Pipeline p = jedis.pipelined();
            for (final Integer alertId : ids) {
                alertIds.add(alertId);
                results.add(ResponseHolder.create(alertId, p.smembers(RedisPattern.alertEntities(alertId))));
            }

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }
    }

    private List<Alert> fetchAlertsById(final Set<Integer> ids) {
        Preconditions.checkNotNull(ids, "ids");

        final List<Alert> alerts = new LinkedList<>();

        if (!ids.isEmpty()) {
            final List<Integer> alertIds = new LinkedList<>();
            final List<ResponseHolder<Integer, Set<String>>> results = new LinkedList<>();

            getAlertDataFromStorage(ids, alertIds, results);

            // process responses
            if (!alertIds.isEmpty()) {

                // get alert definitions from database
                final List<AlertDefinition> definitions = alertDefinintionSProc.getAlertDefinitions(
                        DefinitionStatus.ACTIVE, alertIds);
                if (!definitions.isEmpty()) {

                    // index all definitions
                    final Map<Integer, AlertDefinition> mappedAlerts = Maps.uniqueIndex(definitions,
                            uniqueAlertDefinitionFunction);

                    // process alerts
                    for (final ResponseHolder<Integer, Set<String>> entry : results) {
                        final AlertDefinition def = mappedAlerts.get(entry.getKey());
                        if (def != null) {
                            alerts.add(buildAlert(entry.getKey(), entry.getResponse().get(), def));
                        }
                    }
                }
            }
        }

        return alerts;
    }

    protected void getActiveAlertsForDefinitions(List<AlertDefinition> definitions, List<ResponseHolder<Integer, Set<String>>> results) {
        long start = System.currentTimeMillis();
        final Jedis jedis = redisPool.getResource();
        try {

            // execute async call
            final Pipeline p = jedis.pipelined();
            for (final AlertDefinition definition : definitions) {
                results.add(ResponseHolder.create(definition.getId(),
                        p.smembers(RedisPattern.alertEntities(definition.getId()))));
            }

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }
        long end = System.currentTimeMillis();
        LOG.info("Time taken for {} defs: {}", definitions.size(), end - start);
    }

    @Override
    public List<Alert> getAllAlertsByTeamAndTag(final Set<String> teams, final Set<String> tags) {

        final List<Alert> alerts = new LinkedList<>();

        if (teams != null && !teams.isEmpty() || tags != null && !tags.isEmpty()) {
            final List<AlertDefinition> definitions = getActiveAlertDefinitionByTeamAndTag(teams, tags);
            final List<ResponseHolder<Integer, Set<String>>> results = new LinkedList<>();

            if (!definitions.isEmpty()) {

                getActiveAlertsForDefinitions(definitions, results);

                // TODO remove duplicate code
                // TODO move redis calls to a different service
                // TODO abstract connection management with command pattern/template
                // TODO remove ResponseHolder and use a Map (alerts should be ordered on the webpage)
                //
                // index all definitions
                final Map<Integer, AlertDefinition> mappedAlerts = Maps.uniqueIndex(definitions,
                        uniqueAlertDefinitionFunction);

                // process alerts
                for (final ResponseHolder<Integer, Set<String>> entry : results) {
                    final AlertDefinition def = mappedAlerts.get(entry.getKey());

                    final Set<String> entities = entry.getResponse().get();
                    if (!entities.isEmpty()) {
                        alerts.add(buildAlert(entry.getKey(), entities, def));
                    }
                }
            }
        }

        return alerts;
    }

    @Override
    public Alert getAlert(final int alertId) {

        // get alert definitions from database
        final List<AlertDefinition> definitions = alertDefinintionSProc.getAlertDefinitions(DefinitionStatus.ACTIVE,
                Collections.singletonList(alertId));

        Alert alertResult = null;
        if (!definitions.isEmpty()) {

            Set<String> alertEntities;
            final Jedis jedis = redisPool.getResource();
            try {
                alertEntities = jedis.smembers(RedisPattern.alertEntities(alertId));
            } finally {
                redisPool.returnResource(jedis);
            }

            alertResult = buildAlert(alertId, alertEntities, definitions.get(0));

        }

        return alertResult;
    }

    @Override
    public AlertComment addComment(final AlertComment comment) throws ZMonException {
        Preconditions.checkNotNull(comment, "comment");
        LOG.info("Adding new comment to alert definition '{}'", comment.getAlertDefinitionId());

        final AlertComment result = this.alertDefinintionSProc.addAlertComment(comment).getEntity();

        EVENT_LOG.log(ZMonEventType.ALERT_COMMENT_CREATED, result.getId(), result.getComment(),
            result.getAlertDefinitionId(), result.getEntityId(), result.getCreatedBy());

        return result;
    }

    @Override
    public List<AlertComment> getComments(final int alertDefinitionId, final int limit, final int offset) {
        return alertDefinintionSProc.getAlertComments(alertDefinitionId, limit, offset);
    }

    @Override
    public void deleteAlertComment(final int id) {
        LOG.info("Deleting comment with id '{}'", id);

        final AlertComment comment = alertDefinintionSProc.deleteAlertComment(id);

        if (comment != null) {
            EVENT_LOG.log(ZMonEventType.ALERT_COMMENT_REMOVED, comment.getId(), comment.getComment(),
                comment.getAlertDefinitionId(), comment.getEntityId(), comment.getCreatedBy());
        }
    }

    @Override
    public AlertDefinition getAlertDefinitionNode(final int alertDefinitionId) {
        return alertDefinintionSProc.getAlertDefinitionNode(alertDefinitionId);
    }

    @Override
    public List<AlertDefinition> getAlertDefinitionChildren(final int alertDefinitionId) {
        return alertDefinintionSProc.getAlertDefinitionChildren(alertDefinitionId);
    }

    @Override
    public void forceAlertEvaluation(final int alertDefinitionId) {

        // generate id
        final String id = UUID.randomUUID().toString();

        // build the json
        final ObjectNode node = mapper.createObjectNode();
        node.put("alert_definition_id", alertDefinitionId);

        final String json = node.toString();

        final Jedis jedis = redisPool.getResource();
        try {
            final Pipeline p = jedis.pipelined();
            p.hset(RedisPattern.alertEvaluationQueue(), id, json);

            // expire queue. The scheduler might be down
            p.expire(RedisPattern.alertEvaluationQueue(), INSTANTANEOUS_ALERT_EVALUATION_TIME);
            p.publish(RedisPattern.alertEvaluationChannel(), id);

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }

        EVENT_LOG.log(ZMonEventType.INSTANTANEOUS_ALERT_EVALUATION_SCHEDULED, alertDefinitionId,
            authorityService.getUserName());
    }

    @Override
    public List<String> getAllTags() {
        return alertDefinintionSProc.getAllTags();
    }

    private List<AlertDefinition> getActiveAlertDefinitionByTeamAndTag(final Set<String> teams,
            final Set<String> tags) {

        List<String> teamList = null;
        if (teams != null) {

            // SP doesn't support sets
            teamList = new ArrayList<>(teams.size());
            for (final String team : teams) {
                teamList.add(DBUtil.expandExpression(team));
            }
        }

        List<String> tagList = null;
        if (tags != null) {

            // SP doesn't support sets
            tagList = new ArrayList<>(tags);
        }

        // get alert definitions filtered by team from the database
        return alertDefinintionSProc.getAlertDefinitionsByTeamAndTag(DefinitionStatus.ACTIVE, teamList, tagList);
    }

    protected void getAlertEntityData(Integer alertId, Set<String> entities, List<ResponseHolder<String, String>> results) {
        final Jedis jedis = redisPool.getResource();
        try {

            // execute async call
            final Pipeline p = jedis.pipelined();
            for (final String entity : entities) {
                results.add(ResponseHolder.create(entity, p.get(RedisPattern.alertResult(alertId, entity))));
            }

            p.sync();
        } finally {
            redisPool.returnResource(jedis);
        }
    }

    protected Alert buildAlert(final Integer alertId, final Set<String> entities, final AlertDefinition definition) {
        final List<LastCheckResult> checkResults = new LinkedList<>();

        if (!entities.isEmpty()) {
            final List<ResponseHolder<String, String>> results = new LinkedList<>();

            getAlertEntityData(alertId, entities, results);

            // process results
            for (final ResponseHolder<String, String> entry : results) {
                final String result = entry.getResponse().get();

                // alert result might not be there (worker updated might be in progress )
                if (result != null) {
                    try {
                        checkResults.add(new LastCheckResult(entry.getKey(), mapper.readTree(result)));
                    } catch (final IOException e) {
                        throw new SerializationException("Could not read JSON: " + result, e);
                    }
                }
            }
        }

        final Alert alert = new Alert();
        final AlertDefinitionAuth definitionAuth = AlertDefinitionAuth.from(definition,
                authorityService.hasEditAlertDefinitionPermission(definition),
                authorityService.hasAddAlertDefinitionPermission(),
                authorityService.hasDeleteAlertDefinitionPermission(definition));

        alert.setAlertDefinition(definitionAuth);
        alert.setEntities(checkResults);
        alert.setMessage(buildMessage(definition.getName(), checkResults));

        return alert;
    }

    private String buildMessage(final String template, final List<LastCheckResult> checkResults) {
        String result = template;

        if (!checkResults.isEmpty()) {
            final Set<String> entities = Sets.newHashSetWithExpectedSize(checkResults.size());
            final Map<String, Collection<String>> parameters = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);

            for (final LastCheckResult checkResult : checkResults) {
                final JsonNode node = checkResult.getResult().get(DOWNTIMES_KEY);

                // get captures from an entity not in downtime
                if (node == null || node.size() == 0) {
                    entities.add(checkResult.getEntity());

                    final JsonNode jsonNode = checkResult.getResult().get(CAPTURES_KEY);
                    if (jsonNode != null && jsonNode.isObject()) {
                        final Iterator<Map.Entry<String, JsonNode>> fieldIterator = jsonNode.fields();
                        while (fieldIterator.hasNext()) {
                            final Map.Entry<String, JsonNode> entry = fieldIterator.next();
                            Collection<String> values = parameters.get(entry.getKey());
                            if (values == null) {
                                values = new TreeSet<>();
                                parameters.put(entry.getKey(), values);
                            }

                            values.add(entry.getValue().toString());
                        }
                    }
                }
            }

            parameters.put(ENTITIES_PLACEHOLDER, entities);
            result = messageFormatter.format(result, parameters);
        }

        return result;
    }
}
