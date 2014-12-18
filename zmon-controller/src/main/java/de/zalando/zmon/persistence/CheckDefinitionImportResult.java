package de.zalando.zmon.persistence;

import de.zalando.typemapper.annotations.DatabaseField;

import de.zalando.zmon.domain.CheckDefinition;

public class CheckDefinitionImportResult {

    @DatabaseField
    private CheckDefinition entity;

    @DatabaseField
    private boolean newEntity;

    public CheckDefinition getEntity() {
        return entity;
    }

    public void setEntity(final CheckDefinition entity) {
        this.entity = entity;
    }

    public boolean isNewEntity() {
        return newEntity;
    }

    public void setNewEntity(final boolean newEntity) {
        this.newEntity = newEntity;
    }
}
