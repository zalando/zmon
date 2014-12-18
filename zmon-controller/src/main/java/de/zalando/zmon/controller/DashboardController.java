package de.zalando.zmon.controller;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;

import de.zalando.zmon.domain.Dashboard;
import de.zalando.zmon.domain.DashboardAuth;
import de.zalando.zmon.domain.EditOption;
import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.DashboardService;

@Controller
public class DashboardController extends AbstractZMonController {

    @Autowired
    private DashboardService service;

    @Autowired
    private ZMonAuthorityService authorityService;

    @RequestMapping(value = "dashboard", method = RequestMethod.GET)
    public ResponseEntity<DashboardAuth> getDashboard(@RequestParam(value = "id", required = true) final int id) {

        final List<Dashboard> dashboards = service.getDashboards(Lists.newArrayList(id));
        if (dashboards.isEmpty()) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }

        return new ResponseEntity<>(addDashboardPermissions(dashboards.get(0)), HttpStatus.OK);
    }

    @ResponseBody
    @RequestMapping(value = "deleteDashboard", method = RequestMethod.DELETE)
    public void deleteDashboard(@RequestParam(value = "id", required = true) final int id) throws ZMonException {
        this.service.deleteDashboard(id);
    }

    @RequestMapping(value = "allDashboards", method = RequestMethod.GET)
    public ResponseEntity<List<DashboardAuth>> getAllDashboards() {

        List<DashboardAuth> response = Collections.emptyList();

        final List<Dashboard> dashboards = service.getAllDashboards();

        if (dashboards != null && !dashboards.isEmpty()) {
            response = new ArrayList<>(dashboards.size());
            for (final Dashboard dashboard : dashboards) {
                response.add(addDashboardPermissions(dashboard));
            }
        }

        return new ResponseEntity<>(response, HttpStatus.OK);
    }

    @RequestMapping(value = "updateDashboard", method = RequestMethod.POST)
    public ResponseEntity<Integer> updateDashboard(@Valid
            @RequestBody(required = true)
            final Dashboard dashboard) throws ZMonException {

        final String currentUser = authorityService.getUserName();
        if (dashboard.getId() == null) {
            dashboard.setCreatedBy(currentUser);
        }

        dashboard.setLastModifiedBy(currentUser);

        // check security
        authorityService.verifyEditDashboardPermission(dashboard);

        // if dashboard is shared with the team, set user teams
        final List<String> sharedTeams = dashboard.getEditOption() == EditOption.TEAM
            ? ImmutableList.copyOf(authorityService.getTeams()) : ImmutableList.<String>of();
        dashboard.setSharedTeams(sharedTeams);

        return new ResponseEntity<>(service.createOrUpdateDashboard(dashboard).getId(), HttpStatus.OK);
    }

    private DashboardAuth addDashboardPermissions(final Dashboard dashboard) {
        return DashboardAuth.from(dashboard, authorityService.hasEditDashboardPermission(dashboard),
                authorityService.hasAddDashboardPermission(),
                authorityService.hasDashboardEditModePermission(dashboard));
    }
}
