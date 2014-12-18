package de.zalando.zmon.service.impl;

import de.zalando.zmon.appconfig.ZMonServiceConfig;
import de.zalando.zmon.domain.*;
import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.service.AlertService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import javax.annotation.Nullable;
import java.util.List;
import java.util.Set;

/**
 * Created by jmussler on 10/27/14.
 */
@Service("alert-service-switch")
public class AlertServiceSwitch implements AlertService {

    @Autowired
    private ZMonServiceConfig serviceConfig;

    @Autowired
    @Qualifier("alert-service-redis")
    private AlertService redisService;

    @Override
    public List<AlertDefinition> getAllAlertDefinitions() {
        return redisService.getAllAlertDefinitions();
    }

    @Override
    public List<AlertDefinition> getAlertDefinitions(@Nullable DefinitionStatus status, List<Integer> alertDefinitionIds) {
        return redisService.getAlertDefinitions(status,alertDefinitionIds);
    }

    @Override
    public List<AlertDefinition> getAlertDefinitions(@Nullable DefinitionStatus status, Set<String> teams) {
        return redisService.getAlertDefinitions(status, teams);
    }

    @Override
    public AlertDefinitions getActiveAlertDefinitionsDiff() {
        return redisService.getActiveAlertDefinitionsDiff();
    }

    @Override
    public AlertDefinitionsDiff getAlertDefinitionsDiff(@Nullable Long snapshotId) {
        return redisService.getAlertDefinitionsDiff(snapshotId);
    }

    @Override
    public List<Alert> getAllAlerts() {
        return redisService.getAllAlerts();
    }

    @Override
    public List<Alert> getAllAlertsById(Set<Integer> alertIdfilter) {
        return redisService.getAllAlertsById(alertIdfilter);
    }

    @Override
    public List<Alert> getAllAlertsByTeamAndTag(Set<String> teams, Set<String> tags) {
        return redisService.getAllAlertsByTeamAndTag(teams, tags);
    }

    @Override
    public Alert getAlert(int alertId) {
        return redisService.getAlert(alertId);
    }

    @Override
    public AlertDefinition createOrUpdateAlertDefinition(AlertDefinition alertDefinition) throws ZMonException {
        return redisService.createOrUpdateAlertDefinition(alertDefinition);
    }

    @Override
    public AlertDefinition deleteAlertDefinition(int id) throws ZMonException {
        return redisService.deleteAlertDefinition(id);
    }

    @Override
    public AlertComment addComment(AlertComment comment) throws ZMonException {
        return redisService.addComment(comment);
    }

    @Override
    public List<AlertComment> getComments(int alertDefinitionId, int limit, int offset) {
        return redisService.getComments(alertDefinitionId, limit, offset);
    }

    @Override
    public void deleteAlertComment(int id) {
        redisService.deleteAlertComment(id);
    }

    @Override
    public AlertDefinition getAlertDefinitionNode(int alertDefinitionId) {
        return redisService.getAlertDefinitionNode(alertDefinitionId);
    }

    @Override
    public List<AlertDefinition> getAlertDefinitionChildren(int alertDefinitionId) {
        return redisService.getAlertDefinitionChildren(alertDefinitionId);
    }

    @Override
    public void forceAlertEvaluation(int alertDefinitionId) {
        redisService.forceAlertEvaluation(alertDefinitionId);
    }

    @Override
    public List<String> getAllTags() {
        return redisService.getAllTags();
    }
}
