package de.zalando.zmon.persistence;

import de.zalando.typemapper.annotations.DatabaseField;

import de.zalando.zmon.domain.AlertDefinition;

public class AlertDefinitionOperationResult extends OperationResult {

    @DatabaseField
    private AlertDefinition entity;

    public AlertDefinition getEntity() {
        return entity;
    }

    public void setEntity(final AlertDefinition entity) {
        this.entity = entity;
    }
}
