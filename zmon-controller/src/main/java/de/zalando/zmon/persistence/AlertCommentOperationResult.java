package de.zalando.zmon.persistence;

import de.zalando.typemapper.annotations.DatabaseField;

import de.zalando.zmon.domain.AlertComment;
import de.zalando.zmon.exception.ZMonException;

public class AlertCommentOperationResult extends OperationResult {

    @DatabaseField
    private AlertComment entity;

    public AlertComment getEntity() throws ZMonException {
        throwExceptionOnFailure();
        return entity;
    }

    public void setEntity(final AlertComment entity) {
        this.entity = entity;
    }

}
