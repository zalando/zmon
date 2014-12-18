package de.zalando.zmon.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import de.zalando.zmon.appconfig.ZMonServiceConfig;
import de.zalando.zmon.domain.*;
import de.zalando.zmon.service.ZMonService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import javax.annotation.Nullable;
import java.util.List;
import java.util.Set;

/**
 * Created by jmussler on 10/21/14.
 */
@Service("zmon-service-switch")
public class ZMonServiceSwitch implements ZMonService {

    @Autowired
    private ZMonServiceConfig serviceConfig;

    @Autowired
    @Qualifier("zmon-redis-service")
    private ZMonService redisService;

    @Override
    public ExecutionStatus getStatus() {
        return redisService.getStatus();
    }

    @Override
    public List<String> getAllTeams() {
        return redisService.getAllTeams();
    }

    @Override
    public CheckDefinitions getCheckDefinitions(@Nullable DefinitionStatus status) {
        return redisService.getCheckDefinitions(status);
    }

    @Override
    public List<CheckDefinition> getCheckDefinitions(@Nullable DefinitionStatus status, List<Integer> checkDefinitionIds) {
        return redisService.getCheckDefinitions(status, checkDefinitionIds);
    }

    @Override
    public List<CheckDefinition> getCheckDefinitions(@Nullable DefinitionStatus status, Set<String> teams) {
        return redisService.getCheckDefinitions(status, teams);
    }

    @Override
    public CheckDefinitionsDiff getCheckDefinitionsDiff(Long snapshotId) {
        return redisService.getCheckDefinitionsDiff(snapshotId);
    }

    @Override
    public List<CheckResults> getCheckResults(int checkId, String entity, int limit) {
        return redisService.getCheckResults(checkId, entity, limit);
    }

    @Override
    public List<CheckResults> getCheckAlertResults(int alertId, int limit) {
        return redisService.getCheckAlertResults(alertId, limit);
    }

    @Override
    public CheckDefinition createOrUpdateCheckDefinition(CheckDefinitionImport checkDefinition) {
        return redisService.createOrUpdateCheckDefinition(checkDefinition);
    }

    @Override
    public void deleteCheckDefinition(String userName, String name, String owningTeam) {
        redisService.deleteCheckDefinition(userName, name, owningTeam);
    }

    @Override
    public void deleteDetachedCheckDefinitions() {
        redisService.deleteDetachedCheckDefinitions();
    }

    @Override
    public JsonNode getEntityProperties() {
        return redisService.getEntityProperties();
    }
}
