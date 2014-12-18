package de.zalando.zmon.controller;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.servlet.ModelAndView;

import com.google.common.base.Joiner;

import de.zalando.zmon.security.ZMonAuthorityService;

@Controller
public class ZMonControllerService extends AbstractZMonController {

    private static final Joiner COMMA_JOINER = Joiner.on(',');

    // parameters
    private static final String HAS_SCHEDULE_DOWNTIME_PERMISSION = "hasScheduleDowntimePermission";
    private static final String HAS_DELETE_DOWNTIME_PERMISSION = "hasDeleteDowntimePermission";
    private static final String HAS_TRIAL_RUN_PERMISSION = "hasTrialRunPermission";
    private static final String HAS_ADD_COMMENT_PERMISSION = "hasAddCommentPermission";
    private static final String HAS_ADD_ALERT_DEFINITION_PERMISSION = "hasAddAlertDefinitionPermission";
    private static final String HAS_ADD_DASHBOARD_PERMISSION = "hasAddDashboardPermission";
    private static final String HAS_HISTORY_REPORT_ACCESS = "hasHistoryReportAccess";
    private static final String HAS_INSTANTANEOUS_ALERT_EVALUATION_PERMISSION =
        "hasInstantaneousAlertEvaluationPermission";

    private static final String USER_NAME = "userName";
    private static final String TEAMS = "teams";

    // views
    private static final String INDEX = "/index.jsp";

    @Autowired
    private ZMonAuthorityService authorityService;

    @RequestMapping(value = "index.html", method = RequestMethod.GET)
    public ModelAndView index() {

        // TODO load all permissions in a single shot
        return new ModelAndView(INDEX).addObject(USER_NAME, authorityService.getUserName())
                                      .addObject(TEAMS, COMMA_JOINER.join(authorityService.getTeams()))
                                      .addObject(HAS_SCHEDULE_DOWNTIME_PERMISSION,
                                          authorityService.hasScheduleDowntimePermission())
                                      .addObject(HAS_DELETE_DOWNTIME_PERMISSION,
                                          authorityService.hasDeleteDowntimePermission())
                                      .addObject(HAS_TRIAL_RUN_PERMISSION, authorityService.hasTrialRunPermission())
                                      .addObject(HAS_ADD_COMMENT_PERMISSION, authorityService.hasAddCommentPermission())
                                      .addObject(HAS_ADD_ALERT_DEFINITION_PERMISSION,
                                          authorityService.hasAddAlertDefinitionPermission())
                                      .addObject(HAS_ADD_DASHBOARD_PERMISSION,
                                          authorityService.hasAddDashboardPermission())
                                      .addObject(HAS_HISTORY_REPORT_ACCESS, authorityService.hasHistoryReportAccess())
                                      .addObject(HAS_INSTANTANEOUS_ALERT_EVALUATION_PERMISSION,
                                          authorityService.hasInstantaneousAlertEvaluationPermission());
    }
}
