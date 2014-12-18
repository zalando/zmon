package de.zalando.zmon.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

import de.zalando.zmon.domain.Activity;
import de.zalando.zmon.domain.ActivityDiff;
import de.zalando.zmon.domain.HistoryReport;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.HistoryService;

@Controller
public class HistoryController extends AbstractZMonController {

    @Autowired
    private HistoryService historyService;

    @Autowired
    private ZMonAuthorityService authorityService;

    @RequestMapping(value = "alertHistory", method = RequestMethod.GET)
    public ResponseEntity<List<Activity>> getHistory(
            @RequestParam(value = "alert_definition_id", required = true) final int alertDefinitionId,
            @RequestParam(value = "limit", required = false) final Integer limit,
            @RequestParam(value = "from", required = false) final Long from,
            @RequestParam(value = "to", required = false) final Long to) {

        return new ResponseEntity<>(historyService.getHistory(alertDefinitionId, limit, from, to), HttpStatus.OK);
    }

    @RequestMapping(value = "alertDefinitionHistory", method = RequestMethod.GET)
    public ResponseEntity<List<ActivityDiff>> getAlertDefinitionHistory(
            @RequestParam(value = "alert_definition_id", required = true) final int alertDefinitionId,
            @RequestParam(value = "limit", required = false) final Integer limit,
            @RequestParam(value = "from", required = false) final Long from,
            @RequestParam(value = "to", required = false) final Long to) {

        return new ResponseEntity<>(historyService.getAlertDefinitionHistory(alertDefinitionId, limit, from, to),
                HttpStatus.OK);
    }

    @RequestMapping(value = "checkDefinitionHistory", method = RequestMethod.GET)
    public ResponseEntity<List<ActivityDiff>> getCheckDefinitionHistory(
            @RequestParam(value = "check_definition_id", required = true) final int checkDefinitionId,
            @RequestParam(value = "limit", required = false) final Integer limit,
            @RequestParam(value = "from", required = false) final Long from,
            @RequestParam(value = "to", required = false) final Long to) {

        return new ResponseEntity<>(historyService.getCheckDefinitionHistory(checkDefinitionId, limit, from, to),
                HttpStatus.OK);
    }

    @RequestMapping(value = "historyReport", method = RequestMethod.GET)
    public ResponseEntity<List<HistoryReport>> getHistoryReport(@RequestParam("team") final String team,
            @RequestParam(value = "responsible_team", required = false) final String responsibleTeam,
            @RequestParam(value = "from", required = false) final Long from,
            @RequestParam(value = "to", required = false) final Long to) {

        authorityService.verifyHistoryReportAccess();

        return new ResponseEntity<>(historyService.getHistoryReport(team, responsibleTeam, from, to), HttpStatus.OK);
    }
}
