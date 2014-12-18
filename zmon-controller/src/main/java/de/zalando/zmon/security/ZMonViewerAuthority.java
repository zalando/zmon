package de.zalando.zmon.security;

import java.util.Set;

import org.springframework.security.core.GrantedAuthority;

import com.google.common.collect.ImmutableSet;

import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.Dashboard;

public class ZMonViewerAuthority extends AbstractZMonAuthority {

    private static final long serialVersionUID = 1L;

    public static final GrantedAuthorityFactory FACTORY = new GrantedAuthorityFactory() {
        @Override
        public GrantedAuthority create(final String username, final Set<String> projects) {
            return new ZMonViewerAuthority(username, ImmutableSet.copyOf(projects));
        }
    };

    public ZMonViewerAuthority(final String userName, final ImmutableSet<String> teams) {
        super(userName, teams);
    }

    @Override
    public boolean hasTrialRunPermission() {
        return false;
    }

    @Override
    public boolean hasAddCommentPermission() {
        return false;
    }

    @Override
    public boolean hasDeleteCommentPermission(final AlertComment comment) {
        return false;
    }

    @Override
    public boolean hasScheduleDowntimePermission() {
        return false;
    }

    @Override
    public boolean hasDeleteDowntimePermission() {
        return false;
    }

    @Override
    public boolean hasAddDashboardPermission() {
        return false;
    }

    @Override
    public boolean hasEditDashboardPermission(final Dashboard dashboard) {
        return false;
    }

    @Override
    public boolean hasDashboardEditModePermission(final Dashboard dashboard) {
        return false;
    }

    @Override
    public boolean hasAddAlertDefinitionPermission() {
        return false;
    }

    @Override
    public boolean hasAddAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        return false;
    }

    @Override
    public boolean hasEditAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        return false;
    }

    @Override
    public boolean hasUpdateAlertDefinitionPermission(final AlertDefinition currentAlertDefinition,
            final AlertDefinition newAlertDefinitionDefinition) {
        return false;
    }

    @Override
    public boolean hasDeleteAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        return false;
    }

    @Override
    public boolean hasHistoryReportAccess() {
        return true;
    }

    @Override
    public boolean hasInstantaneousAlertEvaluationPermission() {
        return false;
    }

    @Override
    protected ZMonRole getZMonRole() {
        return ZMonRole.VIEWER;
    }

}
