package de.zalando.zmon.controller;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.common.collect.Lists;

import de.zalando.zmon.domain.Alert;
import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertCommentAuth;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.AlertDefinitionAuth;
import de.zalando.zmon.domain.InstantaneousAlertEvaluationRequest;
import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.AlertService;

@Controller
public class AlertController extends AbstractZMonController {

    @Autowired
    private AlertService service;

    @Autowired
    private ZMonAuthorityService authorityService;

    @RequestMapping(value = "allAlerts", method = RequestMethod.GET)
    public ResponseEntity<List<Alert>> getAllAlerts(
            @RequestParam(value = "team", required = false) final Set<String> teams,
            @RequestParam(value = "tags", required = false) final Set<String> tags) {
        final List<Alert> alerts = teams == null && tags == null ? service.getAllAlerts()
                                                                 : service.getAllAlertsByTeamAndTag(teams, tags);

        return new ResponseEntity<>(alerts, HttpStatus.OK);
    }

    @RequestMapping(value = "alertsById", method = RequestMethod.GET)
    public ResponseEntity<List<Alert>> getAlertsById(
            @RequestParam(value = "id", required = true) final Set<Integer> ids) {

        return new ResponseEntity<>(service.getAllAlertsById(ids), HttpStatus.OK);
    }

    @RequestMapping(value = "alertDetails", method = RequestMethod.GET)
    public ResponseEntity<Alert> getAlert(@RequestParam(value = "alert_id", required = true) final Integer alertId) {
        final Alert alert = service.getAlert(alertId);

        return alert == null ? new ResponseEntity<Alert>(HttpStatus.NOT_FOUND)
                             : new ResponseEntity<>(alert, HttpStatus.OK);
    }

    @RequestMapping(value = "alertDefinitions", method = RequestMethod.GET)
    public ResponseEntity<List<AlertDefinitionAuth>> getAllAlertDefinitions(
            @RequestParam(value = "team", required = false) final Set<String> teams) {
        List<AlertDefinitionAuth> response = Collections.emptyList();

        final List<AlertDefinition> defs = teams == null ? service.getAllAlertDefinitions()
                                                         : service.getAlertDefinitions(null, teams);

        if (defs != null && !defs.isEmpty()) {
            response = new ArrayList<>(defs.size());
            for (final AlertDefinition def : defs) {
                response.add(resolveAlertDefinitionAuth(def));
            }
        }

        return new ResponseEntity<>(response, HttpStatus.OK);
    }

    private AlertDefinitionAuth resolveAlertDefinitionAuth(final AlertDefinition def) {
        return AlertDefinitionAuth.from(def, authorityService.hasEditAlertDefinitionPermission(def),
                authorityService.hasAddAlertDefinitionPermission(),
                authorityService.hasDeleteAlertDefinitionPermission(def));
    }

    @RequestMapping(value = "alertDefinition", method = RequestMethod.GET)
    public ResponseEntity<AlertDefinitionAuth> getAlertDefinition(
            @RequestParam(value = "id", required = true) final int id) {

        final List<AlertDefinition> alertDefinitions = service.getAlertDefinitions(null, Lists.newArrayList(id));
        if (alertDefinitions.isEmpty()) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }

        final AlertDefinition def = alertDefinitions.get(0);
        return new ResponseEntity<>(resolveAlertDefinitionAuth(def), HttpStatus.OK);
    }

    @RequestMapping(value = "alertDefinitionNode", method = RequestMethod.GET)
    public ResponseEntity<AlertDefinitionAuth> getAlertDefinitionNode(
            @RequestParam(value = "id", required = true) final int id) {

        final AlertDefinition node = service.getAlertDefinitionNode(id);
        if (node == null) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }

        return new ResponseEntity<>(resolveAlertDefinitionAuth(node), HttpStatus.OK);
    }

    @RequestMapping(value = "alertDefinitionChildren", method = RequestMethod.GET)
    public ResponseEntity<List<AlertDefinitionAuth>> getAlertDefinitionChildren(
            @RequestParam(value = "id", required = true) final int id) {

        List<AlertDefinitionAuth> response = Collections.emptyList();
        final List<AlertDefinition> defs = service.getAlertDefinitionChildren(id);

        if (defs != null && !defs.isEmpty()) {
            response = new ArrayList<>(defs.size());
            for (final AlertDefinition def : defs) {
                response.add(resolveAlertDefinitionAuth(def));
            }
        }

        return new ResponseEntity<>(response, HttpStatus.OK);
    }

    @RequestMapping(value = "updateAlertDefinition", method = RequestMethod.POST)
    public ResponseEntity<AlertDefinitionAuth> updateAlertDefinition(
            @Valid
            @RequestBody(required = true)
            final AlertDefinition alertDefinition) throws ZMonException {

        alertDefinition.setLastModifiedBy(authorityService.getUserName());

        // check security
        authorityService.verifyEditAlertDefinitionPermission(alertDefinition);

        return new ResponseEntity<>(resolveAlertDefinitionAuth(service.createOrUpdateAlertDefinition(alertDefinition)),
                HttpStatus.OK);
    }

    @ResponseBody
    @RequestMapping(value = "deleteAlertDefinition", method = RequestMethod.DELETE)
    public void deleteAlertDefinition(@RequestParam(value = "id", required = true) final int id) throws ZMonException {
        authorityService.verifyDeleteAlertDefinitionPermission(id);
        service.deleteAlertDefinition(id);
    }

    @RequestMapping(value = "comment", method = RequestMethod.POST)
    public ResponseEntity<AlertCommentAuth> addComment(@Valid
            @RequestBody(required = true)
            final AlertComment comment) throws ZMonException {

        authorityService.verifyAddCommentPermission();

        final String currentUser = authorityService.getUserName();
        comment.setCreatedBy(currentUser);
        comment.setLastModifiedBy(currentUser);

        return new ResponseEntity<>(AlertCommentAuth.from(service.addComment(comment),
                    authorityService.hasDeleteCommentPermission(comment)), HttpStatus.OK);
    }

    @RequestMapping(value = "comments", method = RequestMethod.GET)
    public ResponseEntity<List<AlertCommentAuth>> getComments(
            @RequestParam(value = "alert_definition_id", required = true) final int alertDefinitionId,
            @RequestParam(value = "limit", defaultValue = "20") final int limit,
            @RequestParam(value = "offset", defaultValue = "0") final int offset) {

        final List<AlertComment> currentComments = service.getComments(alertDefinitionId, limit, offset);

        final List<AlertCommentAuth> comments = new LinkedList<>();
        for (final AlertComment comment : currentComments) {
            comments.add(AlertCommentAuth.from(comment, authorityService.hasDeleteCommentPermission(comment)));
        }

        return new ResponseEntity<>(comments, HttpStatus.OK);
    }

    @ResponseBody
    @RequestMapping(value = "deleteComment", method = RequestMethod.DELETE)
    public void deleteComment(@RequestParam(value = "id", required = true) final int id) throws ZMonException {
        authorityService.verifyDeleteCommentPermission(id);
        service.deleteAlertComment(id);
    }

    @ResponseBody
    @RequestMapping(value = "forceAlertEvaluation", method = RequestMethod.POST)
    public void forceAlertEvaluation(@Valid @RequestBody final InstantaneousAlertEvaluationRequest request) {
        authorityService.verifyInstantaneousAlertEvaluationPermission();
        service.forceAlertEvaluation(request.getAlertDefinitionId());
    }

    @RequestMapping(value = "allTags", method = RequestMethod.GET)
    public ResponseEntity<List<String>> getAllTags() {
        return new ResponseEntity<>(service.getAllTags(), HttpStatus.OK);
    }

}
