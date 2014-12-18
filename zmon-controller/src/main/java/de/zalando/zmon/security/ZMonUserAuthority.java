package de.zalando.zmon.security;

import java.util.Set;

import org.springframework.security.core.GrantedAuthority;

import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableSet;

import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.Dashboard;
import de.zalando.zmon.domain.DefinitionStatus;

public class ZMonUserAuthority extends AbstractZMonAuthority {

    private static final long serialVersionUID = 1L;

    public static final GrantedAuthorityFactory FACTORY = new GrantedAuthorityFactory() {
        @Override
        public GrantedAuthority create(final String username, final Set<String> projects) {
            return new ZMonUserAuthority(username, ImmutableSet.copyOf(projects));
        }
    };

    public ZMonUserAuthority(final String userName, final ImmutableSet<String> teams) {
        super(userName, teams);
    }

    @Override
    public boolean hasTrialRunPermission() {
        return true;
    }

    @Override
    public boolean hasAddCommentPermission() {
        return true;
    }

    @Override
    public boolean hasDeleteCommentPermission(final AlertComment comment) {
        Preconditions.checkNotNull(comment, "comment");
        return getUserName().equals(comment.getCreatedBy());
    }

    @Override
    public boolean hasScheduleDowntimePermission() {
        return true;
    }

    @Override
    public boolean hasDeleteDowntimePermission() {
        return true;
    }

    @Override
    public boolean hasAddDashboardPermission() {
        return true;
    }

    @Override
    public boolean hasEditDashboardPermission(final Dashboard dashboard) {
        Preconditions.checkNotNull(dashboard, "dashboard");

        switch (dashboard.getEditOption()) {

            case PUBLIC :
                return true;

            case PRIVATE :
                return getUserName().equals(dashboard.getCreatedBy());

            case TEAM :
                if (dashboard.getSharedTeams() != null) {
                    for (final String team : dashboard.getSharedTeams()) {
                        if (isMemberOfTeam(team)) {
                            return true;
                        }
                    }
                }

            default :
                return false;
        }
    }

    @Override
    public boolean hasDashboardEditModePermission(final Dashboard dashboard) {
        Preconditions.checkNotNull(dashboard, "dashboard");

        return getUserName().equals(dashboard.getCreatedBy());
    }

    @Override
    public boolean hasAddAlertDefinitionPermission() {
        return true;
    }

    @Override
    public boolean hasAddAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        Preconditions.checkNotNull(alertDefinition, "alertDefinition");

        return isMemberOfTeam(alertDefinition.getTeam())
                || isMemberOfTeam(alertDefinition.getResponsibleTeam()) && (alertDefinition.getStatus()
                    == DefinitionStatus.INACTIVE);
    }

    @Override
    public boolean hasEditAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        Preconditions.checkNotNull(alertDefinition, "alertDefinition");

        return isMemberOfTeam(alertDefinition.getTeam())
                || isMemberOfTeam(alertDefinition.getResponsibleTeam()) && (alertDefinition.getStatus() == DefinitionStatus.INACTIVE
                    || alertDefinition.getStatus() == DefinitionStatus.REJECTED);
    }

    @Override
    public boolean hasUpdateAlertDefinitionPermission(final AlertDefinition currentAlertDefinition,
            final AlertDefinition newAlertDefinition) {
        Preconditions.checkNotNull(currentAlertDefinition, "currentAlertDefinition");
        Preconditions.checkNotNull(newAlertDefinition, "newAlertDefinition");

        final DefinitionStatus currentStatus = currentAlertDefinition.getStatus();
        final DefinitionStatus newStatus = newAlertDefinition.getStatus();

        final boolean isMemberOfCurrentTeam = isMemberOfTeam(currentAlertDefinition.getTeam());
        return hasEditAlertDefinitionPermission(currentAlertDefinition)
                && (isMemberOfTeam(newAlertDefinition.getTeam())
                    || (isMemberOfTeam(newAlertDefinition.getResponsibleTeam())
                        && (isMemberOfCurrentTeam && newStatus == DefinitionStatus.INACTIVE
                            || !isMemberOfCurrentTeam && (currentStatus == newStatus
                                || currentStatus == DefinitionStatus.REJECTED && newStatus == DefinitionStatus.INACTIVE))));
    }

    @Override
    public boolean hasDeleteAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        return isMemberOfTeam(alertDefinition.getTeam());
    }

    @Override
    public boolean hasHistoryReportAccess() {
        return true;
    }

    @Override
    public boolean hasInstantaneousAlertEvaluationPermission() {
        return true;
    }

    @Override
    protected ZMonRole getZMonRole() {
        return ZMonRole.USER;
    }
}
