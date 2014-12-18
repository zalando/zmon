package de.zalando.zmon.service.impl;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.LinkedList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.stereotype.Service;

import com.google.common.base.Preconditions;
import com.google.common.primitives.Longs;

import de.zalando.zmon.domain.Activity;
import de.zalando.zmon.domain.ActivityDiff;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.HistoryAction;
import de.zalando.zmon.domain.HistoryEntry;
import de.zalando.zmon.domain.HistoryReport;
import de.zalando.zmon.domain.HistoryType;
import de.zalando.zmon.event.ZMonEventType;
import de.zalando.zmon.persistence.AlertDefinitionSProcService;
import de.zalando.zmon.persistence.CheckDefinitionSProcService;
import de.zalando.zmon.service.HistoryService;
import de.zalando.zmon.util.HistoryUtils;

@Service
public class HistoryServiceImpl implements HistoryService {

    private static final String ZMON_BY_CHECK_ID_USE_CASE = "ZMON_BY_CHECK_ID";

    private static final String ZMON_BY_ALERT_ID_USE_CASE = "ZMON_BY_ALERT_ID";

    private static final int DEFAULT_HISTORY_LIMIT = 50;

    private static final Comparator<Activity> ACTIVITY_TIME_COMPARATOR = new Comparator<Activity>() {

        @Override
        public int compare(final Activity o1, final Activity o2) {
            return Longs.compare(o2.getTime(), o1.getTime());
        }
    };

    @Autowired
    private CheckDefinitionSProcService checkDefinitionSProc;

    @Autowired
    private AlertDefinitionSProcService alertDefinitionSProc;

    @Override
    public List<Activity> getHistory(final int alertDefinitionId, final Integer limit, final Long from, final Long to) {
        final Integer realLimit = resolveLimit(limit, from, to);

        final Long fromMillis = from == null ? null : from * 1000;
        final Long toMillis = to == null ? null : to * 1000;

        List<Activity> history = Collections.emptyList();

        final List<AlertDefinition> definitions = alertDefinitionSProc.getAlertDefinitions(null,
                Collections.singletonList(alertDefinitionId));

        if (!definitions.isEmpty()) {
            /*
            final List<Event> eventsByCheckId = eventLogService.getEventsForUseCaseExtended(ZMON_BY_CHECK_ID_USE_CASE,
                    Collections.singletonList(String.valueOf(definitions.get(0).getCheckDefinitionId())), fromMillis,
                    toMillis, realLimit);

            final List<Event> eventsByAlertId = eventLogService.getEventsForUseCaseExtended(ZMON_BY_ALERT_ID_USE_CASE,
                    Collections.singletonList(String.valueOf(alertDefinitionId)), fromMillis, toMillis, realLimit);
                    

            history = mergeEvents(realLimit, eventsByCheckId, eventsByAlertId);
            */
        }

        return history;
    }

    /*
    private List<Activity> mergeEvents(final Integer limit, final List<Event> eventsByCheckId,
            final List<Event> eventsByAlertId) {

        List<Activity> history = Collections.emptyList();

        final int size = (eventsByCheckId == null ? 0 : eventsByCheckId.size())
                + (eventsByAlertId == null ? 0 : eventsByAlertId.size());

        if (size > 0) {
            final List<Activity> activities = new ArrayList<>(size);
            if (eventsByCheckId != null && !eventsByCheckId.isEmpty()) {
                for (final Event event : eventsByCheckId) {
                    activities.add(createActivity(event));
                }
            }

            if (eventsByAlertId != null && !eventsByAlertId.isEmpty()) {
                for (final Event event : eventsByAlertId) {
                    activities.add(createActivity(event));
                }
            }

            Collections.sort(activities, ACTIVITY_TIME_COMPARATOR);
            history = limit == null ? activities : activities.subList(0, limit);
        }

        return history;
    }
    */

    @Override
    public List<ActivityDiff> getCheckDefinitionHistory(final int checkDefinitionId, final Integer limit,
            final Long from, final Long to) {
        final List<HistoryEntry> databaseHistory = checkDefinitionSProc.getCheckDefinitionHistory(checkDefinitionId,
                resolveLimit(limit, from, to), secondsToDate(from), secondsToDate(to));

        final List<ActivityDiff> history = new LinkedList<>();
        for (final HistoryEntry entry : databaseHistory) {
            history.add(createActivityDiff(entry, resolveCheckDefinitionEventType(entry.getAction())));
        }

        return history;
    }

    @Override
    public List<ActivityDiff> getAlertDefinitionHistory(final int alertDefinitionId, final Integer limit,
            final Long from, final Long to) {
        final List<HistoryEntry> databaseHistory = alertDefinitionSProc.getAlertDefinitionHistory(alertDefinitionId,
                resolveLimit(limit, from, to), secondsToDate(from), secondsToDate(to));

        final List<ActivityDiff> history = new LinkedList<>();
        for (final HistoryEntry entry : databaseHistory) {
            history.add(createActivityDiff(entry, resolveAlertDefinitionEventType(entry.getAction())));
        }

        return history;
    }

    @Override
    public List<HistoryReport> getHistoryReport(final String team, final String responsibleTeam, final Long from,
            final Long to) {
        return getHistoryReport(team, responsibleTeam, DEFAULT_HISTORY_LIMIT, DEFAULT_HISTORY_LIMIT, from, to);
    }

    @Override
    public List<HistoryReport> getHistoryReport(final String team, final String responsibleTeam, final int alertLimit,
            final int checkLimit, final Long from, final Long to) {
        Preconditions.checkNotNull(team);

        List<HistoryReport> history = Collections.emptyList();

        final List<HistoryEntry> databaseHistory = alertDefinitionSProc.getHistoryReport(team, responsibleTeam,
                alertLimit, checkLimit, secondsToDate(from), secondsToDate(to));

        if (!databaseHistory.isEmpty()) {
            history = new ArrayList<>(databaseHistory.size());
            for (final HistoryEntry entry : databaseHistory) {
                history.add(createHistoryReport(entry, resolveEventType(entry.getAction(), entry.getHistoryType())));
            }

            Collections.sort(history, ACTIVITY_TIME_COMPARATOR);
        }

        return history;
    }

    private Integer resolveLimit(final Integer limit, final Long from, final Long to) {
        return limit != null ? limit : from == null && to == null ? DEFAULT_HISTORY_LIMIT : null;
    }

    private Date secondsToDate(final Long time) {
        return time == null ? null : new Date(time * 1000);
    }

    private long dateToSeconds(final Date date) {
        return date.getTime() / 1000;
    }

    /*
    private Activity createActivity(final Event event) {
        final Activity activity = new Activity();
        activity.setTime(dateToSeconds(event.getTime()));
        activity.setTypeId(event.getTypeId());
        activity.setTypeName(event.getTypeName());
        activity.setAttributes(event.getAttributes());

        return activity;
    }
    */

    private ActivityDiff createActivityDiff(final HistoryEntry entry, final ZMonEventType eventType) {
        return fillActivityDiff(new ActivityDiff(), entry, eventType);
    }

    private ActivityDiff fillActivityDiff(final ActivityDiff activity, final HistoryEntry entry,
            final ZMonEventType eventType) {
        activity.setTime(dateToSeconds(entry.getTimestamp()));
        activity.setTypeId(eventType.getId());
        activity.setTypeName(eventType.getName());
        activity.setAttributes(entry.getRowData());
        activity.setRecordId(entry.getRecordId());
        activity.setAction(entry.getAction());
        activity.setChangedAttributes(entry.getChangedFields());
        activity.setLastModifiedBy(HistoryUtils.resolveModifiedBy(entry.getRowData(), entry.getChangedFields()));

        return activity;
    }

    private HistoryReport createHistoryReport(final HistoryEntry entry, final ZMonEventType eventType) {
        final HistoryReport report = new HistoryReport();

        fillActivityDiff(report, entry, eventType);
        report.setHistoryType(entry.getHistoryType());

        return report;
    }

    private ZMonEventType resolveCheckDefinitionEventType(final HistoryAction action) {

        switch (action) {

            case INSERT :
                return ZMonEventType.CHECK_DEFINITION_CREATED;

            case UPDATE :
                return ZMonEventType.CHECK_DEFINITION_UPDATED;

            default :
                throw new IllegalArgumentException("Action not supported: " + action);
        }
    }

    private ZMonEventType resolveAlertDefinitionEventType(final HistoryAction action) {

        switch (action) {

            case INSERT :
                return ZMonEventType.ALERT_DEFINITION_CREATED;

            case UPDATE :
                return ZMonEventType.ALERT_DEFINITION_UPDATED;

            default :
                throw new IllegalArgumentException("Action not supported: " + action);
        }
    }

    private ZMonEventType resolveEventType(final HistoryAction action, final HistoryType historyType) {
        switch (historyType) {

            case CHECK_DEFINITION :
                return resolveCheckDefinitionEventType(action);

            case ALERT_DEFINITION :
                return resolveAlertDefinitionEventType(action);

            default :
                throw new IllegalArgumentException("History type not supported: " + action);
        }

    }
}
