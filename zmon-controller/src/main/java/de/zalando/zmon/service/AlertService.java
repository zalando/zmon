package de.zalando.zmon.service;

import java.util.List;
import java.util.Set;

import javax.annotation.Nullable;

import de.zalando.zmon.domain.Alert;
import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.AlertDefinitions;
import de.zalando.zmon.domain.AlertDefinitionsDiff;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.exception.ZMonException;

public interface AlertService {

    List<AlertDefinition> getAllAlertDefinitions();

    List<AlertDefinition> getAlertDefinitions(@Nullable DefinitionStatus status, List<Integer> alertDefinitionIds);

    List<AlertDefinition> getAlertDefinitions(@Nullable DefinitionStatus status, Set<String> teams);

    AlertDefinitions getActiveAlertDefinitionsDiff();

    AlertDefinitionsDiff getAlertDefinitionsDiff(@Nullable Long snapshotId);

    List<Alert> getAllAlerts();

    List<Alert> getAllAlertsById(Set<Integer> alertIdfilter);

    List<Alert> getAllAlertsByTeamAndTag(Set<String> teams, Set<String> tags);

    Alert getAlert(int alertId);

    AlertDefinition createOrUpdateAlertDefinition(AlertDefinition alertDefinition) throws ZMonException;

    AlertDefinition deleteAlertDefinition(int id) throws ZMonException;

    AlertComment addComment(AlertComment comment) throws ZMonException;

    List<AlertComment> getComments(int alertDefinitionId, int limit, int offset);

    void deleteAlertComment(int id);

    AlertDefinition getAlertDefinitionNode(int alertDefinitionId);

    List<AlertDefinition> getAlertDefinitionChildren(int alertDefinitionId);

    void forceAlertEvaluation(int alertDefinitionId);

    List<String> getAllTags();
}
