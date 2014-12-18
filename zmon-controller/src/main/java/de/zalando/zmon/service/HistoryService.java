package de.zalando.zmon.service;

import java.util.List;

import javax.annotation.Nullable;

import de.zalando.zmon.domain.Activity;
import de.zalando.zmon.domain.ActivityDiff;
import de.zalando.zmon.domain.HistoryReport;

public interface HistoryService {

    List<Activity> getHistory(int alertDefinitionId, @Nullable Integer limit, @Nullable Long from, @Nullable Long to);

    List<ActivityDiff> getCheckDefinitionHistory(int checkDefinitionId, @Nullable Integer limit, @Nullable Long from,
            @Nullable Long to);

    List<ActivityDiff> getAlertDefinitionHistory(int alertDefinitionId, @Nullable Integer limit, @Nullable Long from,
            @Nullable Long to);

    List<HistoryReport> getHistoryReport(String team, @Nullable String responsibleTeam, @Nullable Long from,
            @Nullable Long to);

    List<HistoryReport> getHistoryReport(String team, @Nullable String responsibleTeam, int alertLimit, int checkLimit,
            @Nullable Long from, @Nullable Long to);
}
