package de.zalando.zmon.redis;

import com.google.common.base.Preconditions;

public final class RedisPattern {

    private static final String KEY_SEPARATOR = ":";

    private static final String REDIS_TRIAL_RUN_PREFIX = "zmon:trial_run";

    private static final String REDIS_TRIAL_RUN_QUEUE = REDIS_TRIAL_RUN_PREFIX + KEY_SEPARATOR + "requests";

    private static final String REDIS_TRIAL_RUN_PUB_SUB = REDIS_TRIAL_RUN_PREFIX + KEY_SEPARATOR + "pubsub";

    private static final String REDIS_DOWNTIME_SCHEDULE_PUB_SUB = "zmon:downtime_schedule:pubsub";

    private static final String REDIS_DOWNTIME_SCHEDULE_QUEUE = "zmon:downtime_schedule:requests";

    private static final String REDIS_DOWNTIME_REMOVE_PUB_SUB = "zmon:downtime_remove:pubsub";

    private static final String REDIS_DOWNTIME_REMOVE_QUEUE = "zmon:downtime_remove:requests";

    private static final String REDIS_INSTANTANEOUS_ALERT_EVALUATION_PUB_SUB = "zmon:alert_evaluation:pubsub";

    private static final String REDIS_INSTANTANEOUS_ALERT_EVALUATION_QUEUE = "zmon:alert_evaluation:requests";

    private static final String REDIS_ALERT_PREFIX = "zmon:alerts";

    private static final String REDIS_CHECK_PREFIX = "zmon:checks";

    private static final String REDIS_METRICS = "zmon:metrics";

    private static final String REDIS_DOWNTIME_PREFIX = "zmon:downtimes";

    private static final String REDIS_METRICS_TIMESTAMP_SUFFIX = "ts";

    private static final String REDIS_METRICS_CHECK_COUNT_SUFFIX = "check.count";

    private static final String ALERT_FILTER_ENTITIES_SUFFIX = "entities";

    private static final String TRIAL_RUN_RESULTS_SUFFIX = "results";

    private static final String ZMON_ENTITY_PROPERTIES = "zmon:entity:properties";

    private RedisPattern() { }

    public static String trialRunQueue() {
        return REDIS_TRIAL_RUN_QUEUE;
    }

    public static String trialRunEntities(final String trialRunId) {
        Preconditions.checkNotNull(trialRunId, "trialRunId");
        return new StringBuilder(REDIS_TRIAL_RUN_PREFIX).append(KEY_SEPARATOR).append(trialRunId).toString();
    }

    public static String trialRunResults(final String trialRunId) {
        Preconditions.checkNotNull(trialRunId, "trialRunId");
        return new StringBuilder(REDIS_TRIAL_RUN_PREFIX).append(KEY_SEPARATOR).append(trialRunId).append(KEY_SEPARATOR)
                                                        .append(TRIAL_RUN_RESULTS_SUFFIX).toString();
    }

    public static String trialRunChannel() {
        return REDIS_TRIAL_RUN_PUB_SUB;
    }

    public static String alertIds() {
        return REDIS_ALERT_PREFIX;
    }

    public static String workerNames() {
        return REDIS_METRICS;
    }

    public static String downtimeAlertIds() {
        return REDIS_DOWNTIME_PREFIX;
    }

    public static String entityProperties() {
        return ZMON_ENTITY_PROPERTIES;
    }

    public static String downtimeEntities(final Integer alertId) {
        Preconditions.checkNotNull(alertId, "alertId");

        // string format is too slow
        return new StringBuilder(REDIS_DOWNTIME_PREFIX).append(KEY_SEPARATOR).append(alertId).toString();
    }

    public static String downtimeDetails(final Integer alertId, final String entityId) {
        Preconditions.checkNotNull(alertId, "alertId");
        Preconditions.checkNotNull(entityId, "entityId");

        // string format is too slow
        return new StringBuilder(REDIS_DOWNTIME_PREFIX).append(KEY_SEPARATOR).append(alertId).append(KEY_SEPARATOR)
                                                       .append(entityId).toString();
    }

    public static String workerLastUpdated(final String workerName) {
        return REDIS_METRICS + KEY_SEPARATOR + workerName + KEY_SEPARATOR + REDIS_METRICS_TIMESTAMP_SUFFIX;
    }

    public static String workerCheckInvocations(final String workerName) {
        return REDIS_METRICS + KEY_SEPARATOR + workerName + KEY_SEPARATOR + REDIS_METRICS_CHECK_COUNT_SUFFIX;
    }

    public static String alertEntities(final Integer alertId) {
        Preconditions.checkNotNull(alertId, "alertId");

        // string format is too slow
        return new StringBuilder(REDIS_ALERT_PREFIX).append(KEY_SEPARATOR).append(alertId).toString();
    }

    public static String alertResult(final Integer alertId, final String entityId) {
        Preconditions.checkNotNull(alertId, "alertId");
        Preconditions.checkNotNull(entityId, "entityId");

        // string format is too slow
        return new StringBuilder(REDIS_ALERT_PREFIX).append(KEY_SEPARATOR).append(alertId).append(KEY_SEPARATOR)
                                                    .append(entityId).toString();
    }

    public static String alertFilterEntities(final Integer alertId) {
        Preconditions.checkNotNull(alertId, "alertId");

        // string format is too slow
        return new StringBuilder(REDIS_ALERT_PREFIX).append(KEY_SEPARATOR).append(alertId).append(KEY_SEPARATOR)
                                                    .append(ALERT_FILTER_ENTITIES_SUFFIX).toString();
    }

    public static String checkEntities(final Integer checkId) {
        Preconditions.checkNotNull(checkId, "checkId");

        // string format is too slow
        return new StringBuilder(REDIS_CHECK_PREFIX).append(KEY_SEPARATOR).append(checkId).toString();
    }

    public static String checkResult(final Integer checkId, final String entityId) {
        Preconditions.checkNotNull(checkId, "checkId");
        Preconditions.checkNotNull(entityId, "entityId");

        // string format is too slow
        return new StringBuilder(REDIS_CHECK_PREFIX).append(KEY_SEPARATOR).append(checkId).append(KEY_SEPARATOR)
                                                    .append(entityId).toString();
    }

    public static String downtimeScheduleChannel() {
        return REDIS_DOWNTIME_SCHEDULE_PUB_SUB;
    }

    public static String downtimeScheduleQueue() {
        return REDIS_DOWNTIME_SCHEDULE_QUEUE;
    }

    public static String downtimeRemoveChannel() {
        return REDIS_DOWNTIME_REMOVE_PUB_SUB;
    }

    public static String downtimeRemoveQueue() {
        return REDIS_DOWNTIME_REMOVE_QUEUE;
    }

    public static String alertEvaluationChannel() {
        return REDIS_INSTANTANEOUS_ALERT_EVALUATION_PUB_SUB;
    }

    public static String alertEvaluationQueue() {
        return REDIS_INSTANTANEOUS_ALERT_EVALUATION_QUEUE;
    }

}
