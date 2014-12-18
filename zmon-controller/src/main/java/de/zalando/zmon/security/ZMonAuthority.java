package de.zalando.zmon.security;

import java.util.Set;

import org.springframework.security.core.GrantedAuthority;

import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.Dashboard;

public interface ZMonAuthority extends GrantedAuthority {

    Set<String> getTeams();

    boolean hasTrialRunPermission();

    boolean hasAddCommentPermission();

    boolean hasDeleteCommentPermission(AlertComment comment);

    boolean hasScheduleDowntimePermission();

    boolean hasDeleteDowntimePermission();

    boolean hasAddDashboardPermission();

    boolean hasEditDashboardPermission(Dashboard dashboard);

    boolean hasDashboardEditModePermission(Dashboard dashboard);

    boolean hasAddAlertDefinitionPermission();

    boolean hasAddAlertDefinitionPermission(AlertDefinition alertDefinition);

    boolean hasEditAlertDefinitionPermission(AlertDefinition alertDefinition);

    boolean hasUpdateAlertDefinitionPermission(AlertDefinition currentAlertDefinition,
            AlertDefinition newAlertDefinitionDefinition);

    boolean hasDeleteAlertDefinitionPermission(AlertDefinition alertDefinition);

    boolean hasHistoryReportAccess();

    boolean hasInstantaneousAlertEvaluationPermission();

}
