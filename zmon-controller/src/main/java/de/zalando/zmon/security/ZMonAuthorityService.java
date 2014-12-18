package de.zalando.zmon.security;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Set;

import javax.annotation.Nonnull;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import org.springframework.stereotype.Service;

import com.google.common.base.Function;
import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableSet;

import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.Dashboard;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.exception.ZMonAuthorizationException;
import de.zalando.zmon.persistence.AlertDefinitionSProcService;
import de.zalando.zmon.persistence.DashboardSProcService;

@Service
public class ZMonAuthorityService {

    private static final Function<ZMonAuthority, Boolean> TRIAL_RUN_PERMISSION_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasTrialRunPermission();
            }
        };

    private static final Function<ZMonAuthority, Boolean> ADD_COMMENT_PERMISSION_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasAddCommentPermission();
            }
        };

    private static final Function<ZMonAuthority, Boolean> ADD_ALERT_DEFINITION_PERMISSION_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasAddAlertDefinitionPermission();
            }
        };

    private static final Function<ZMonAuthority, Boolean> SCHEDULE_DOWNTIME_PERMISSION_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasScheduleDowntimePermission();
            }
        };

    private static final Function<ZMonAuthority, Boolean> DELETE_DOWNTIME_PERMISSION_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasDeleteDowntimePermission();
            }
        };

    private static final Function<ZMonAuthority, Boolean> ADD_DASHBOARD_PERMISSION_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasAddDashboardPermission();
            }
        };

    private static final Function<ZMonAuthority, Boolean> HISTORY_REPORT_ACCESS_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasHistoryReportAccess();
            }
        };

    private static final Function<ZMonAuthority, Boolean> INSTANTANEOUS_ALERT_EVALUATION_FUNCTION =

        new Function<ZMonAuthority, Boolean>() {
            @Override
            public Boolean apply(@Nonnull final ZMonAuthority input) {
                return input.hasInstantaneousAlertEvaluationPermission();
            }
        };

    private static final String ANONYMOUS_USER = "anonymousUser";

    @Autowired
    private AlertDefinitionSProcService alertDefinitionSProc;

    @Autowired
    private DashboardSProcService dashboardSProc;

    public String getUserName() {
        final Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication == null ? ANONYMOUS_USER : authentication.getName();
    }

    public Set<String> getTeams() {
        final ImmutableSet.Builder<String> teams = ImmutableSet.builder();
        for (final GrantedAuthority authority : getUserAuthorities()) {
            if (authority instanceof ZMonAuthority) {
                teams.addAll(((ZMonAuthority) authority).getTeams());
            }
        }

        return teams.build();
    }

    private boolean hasAnyAuthority(final Function<ZMonAuthority, Boolean> function) {
        for (final GrantedAuthority authority : getUserAuthorities()) {
            if (authority instanceof ZMonAuthority && function.apply((ZMonAuthority) authority)) {
                return true;
            }
        }

        return false;
    }

    private Collection<? extends GrantedAuthority> getUserAuthorities() {
        final Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication == null ? Collections.<GrantedAuthority>emptyList() : authentication.getAuthorities();
    }

    public boolean hasTrialRunPermission() {
        return hasAnyAuthority(TRIAL_RUN_PERMISSION_FUNCTION);
    }

    public void verifyTrialRunPermission() {
        if (!hasTrialRunPermission()) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "You are not allowed to use 'trial run' functionality");
        }
    }

    public boolean hasAddCommentPermission() {
        return hasAnyAuthority(ADD_COMMENT_PERMISSION_FUNCTION);
    }

    public void verifyAddCommentPermission() {
        if (!hasAddCommentPermission()) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "You are not allowed to add comments");
        }
    }

    public boolean hasDeleteCommentPermission(final AlertComment comment) {
        Preconditions.checkNotNull(comment, "comment");

        return hasAnyAuthority(new Function<ZMonAuthority, Boolean>() {
                    @Override
                    public Boolean apply(final ZMonAuthority input) {
                        return input.hasDeleteCommentPermission(comment);
                    }
                });
    }

    public void verifyDeleteCommentPermission(final int commentId) {
        final AlertComment comment = alertDefinitionSProc.getAlertCommentById(commentId);

        if (comment == null || !hasDeleteCommentPermission(comment)) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "You are not allowed to delete this comment", commentId);
        }
    }

    public boolean hasAddAlertDefinitionPermission() {
        return hasAnyAuthority(ADD_ALERT_DEFINITION_PERMISSION_FUNCTION);
    }

    public boolean hasEditAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        Preconditions.checkNotNull(alertDefinition, "alertDefinition");

        return hasAnyAuthority(new Function<ZMonAuthority, Boolean>() {
                    @Override
                    public Boolean apply(final ZMonAuthority input) {
                        return input.hasEditAlertDefinitionPermission(alertDefinition);
                    }
                }) && alertDefinition.getStatus() != DefinitionStatus.DELETED;
    }

    public boolean hasDeleteAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        Preconditions.checkNotNull(alertDefinition, "alertDefinition");

        return hasAnyAuthority(new Function<ZMonAuthority, Boolean>() {
                    @Override
                    public Boolean apply(final ZMonAuthority input) {
                        return input.hasDeleteAlertDefinitionPermission(alertDefinition);
                    }
                });
    }

    public void verifyDeleteAlertDefinitionPermission(final int alertDefinitionId) {
        final List<AlertDefinition> definitions = alertDefinitionSProc.getAlertDefinitions(null,
                Collections.singletonList(alertDefinitionId));

        if (definitions == null || definitions.size() != 1 || !hasDeleteAlertDefinitionPermission(definitions.get(0))) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "You are not allowed to delete this alert definition", alertDefinitionId);
        }
    }

    public void verifyEditAlertDefinitionPermission(final AlertDefinition alertDefinition) {
        Preconditions.checkNotNull(alertDefinition, "alertDefinition");

        boolean isAllowed = false;
        if (alertDefinition.getId() == null) {
            isAllowed = hasAnyAuthority(new Function<ZMonAuthority, Boolean>() {
                        @Override
                        public Boolean apply(final ZMonAuthority input) {
                            return input.hasAddAlertDefinitionPermission(alertDefinition);
                        }
                    });
        } else {

            // that's an update... load current alert definition
            final List<AlertDefinition> definitions = alertDefinitionSProc.getAlertDefinitions(null,
                    Collections.singletonList(alertDefinition.getId()));

            isAllowed = definitions.size() == 1 && hasAnyAuthority(new Function<ZMonAuthority, Boolean>() {
                            @Override
                            public Boolean apply(final ZMonAuthority input) {
                                return input.hasUpdateAlertDefinitionPermission(definitions.get(0), alertDefinition);
                            }
                        });
        }

        if (!isAllowed) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "Edit denied. Please check documentation for more details: /docs/permissions.html", alertDefinition);
        }
    }

    public boolean hasScheduleDowntimePermission() {
        return hasAnyAuthority(SCHEDULE_DOWNTIME_PERMISSION_FUNCTION);
    }

    public void verifyScheduleDowntimePermission() {
        if (!hasScheduleDowntimePermission()) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "You are not allowed to schedule downtimes");
        }
    }

    public boolean hasDeleteDowntimePermission() {
        return hasAnyAuthority(DELETE_DOWNTIME_PERMISSION_FUNCTION);
    }

    public void verifyDeleteDowntimePermission() {
        if (!hasDeleteDowntimePermission()) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "You are not allowed to delete downtimes");
        }
    }

    public boolean hasAddDashboardPermission() {
        return hasAnyAuthority(ADD_DASHBOARD_PERMISSION_FUNCTION);
    }

    public boolean hasEditDashboardPermission(final Dashboard dashboard) {
        Preconditions.checkNotNull(dashboard, "dashboard");

        return hasAnyAuthority(new Function<ZMonAuthority, Boolean>() {
                    @Override
                    public Boolean apply(final ZMonAuthority input) {
                        return input.hasEditDashboardPermission(dashboard);
                    }
                });
    }

    public boolean hasDashboardEditModePermission(final Dashboard dashboard) {
        Preconditions.checkNotNull(dashboard, "dashboard");

        return hasAnyAuthority(new Function<ZMonAuthority, Boolean>() {
                    @Override
                    public Boolean apply(final ZMonAuthority input) {
                        return input.hasDashboardEditModePermission(dashboard);
                    }
                });
    }

    public void verifyEditDashboardPermission(final Dashboard dashboard) {
        Preconditions.checkNotNull(dashboard, "dashboard");

        boolean isAllowed = hasAddDashboardPermission();
        if (isAllowed && dashboard.getId() != null) {
            final List<Dashboard> dashboards = dashboardSProc.getDashboards(Collections.singletonList(
                        dashboard.getId()));
            isAllowed = dashboards.size() == 1 && hasEditDashboardPermission(dashboards.get(0))
                    && (hasDashboardEditModePermission(dashboards.get(0))
                        || dashboards.get(0).getEditOption() == dashboard.getEditOption());
        }

        if (!isAllowed) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "Your are not allowed to create/edit this dashboard", dashboard);
        }
    }

    public boolean hasHistoryReportAccess() {
        return hasAnyAuthority(HISTORY_REPORT_ACCESS_FUNCTION);
    }

    public void verifyHistoryReportAccess() {
        if (!hasHistoryReportAccess()) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "Your are not allowed to view reports");
        }
    }

    public boolean hasInstantaneousAlertEvaluationPermission() {
        return hasAnyAuthority(INSTANTANEOUS_ALERT_EVALUATION_FUNCTION);
    }

    public void verifyInstantaneousAlertEvaluationPermission() {
        if (!hasInstantaneousAlertEvaluationPermission()) {
            throw new ZMonAuthorizationException(getUserName(), getUserAuthorities(),
                "Your are not allowed to force alert evaluation");
        }
    }
}
