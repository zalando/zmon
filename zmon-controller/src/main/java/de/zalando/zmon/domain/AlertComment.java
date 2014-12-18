package de.zalando.zmon.domain;

import java.util.Date;

import javax.validation.constraints.NotNull;

import org.hibernate.validator.constraints.NotEmpty;

import de.zalando.typemapper.annotations.DatabaseField;

public class AlertComment {

    @DatabaseField
    private Integer id;

    @DatabaseField
    private Date created;

    @DatabaseField
    private String createdBy;

    @DatabaseField
    private Date lastModified;

    @DatabaseField
    private String lastModifiedBy;

    @NotEmpty(message = "comment is mandatory")
    @DatabaseField
    private String comment;

    @NotNull(message = "alert definition id is mandatory")
    @DatabaseField
    private Integer alertDefinitionId;

    @DatabaseField
    private String entityId;

    public Integer getId() {
        return id;
    }

    public void setId(final Integer id) {
        this.id = id;
    }

    public Date getCreated() {
        return created;
    }

    public void setCreated(final Date created) {
        this.created = created;
    }

    public String getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(final String createdBy) {
        this.createdBy = createdBy;
    }

    public Date getLastModified() {
        return lastModified;
    }

    public void setLastModified(final Date lastModified) {
        this.lastModified = lastModified;
    }

    public String getLastModifiedBy() {
        return lastModifiedBy;
    }

    public void setLastModifiedBy(final String lastModifiedBy) {
        this.lastModifiedBy = lastModifiedBy;
    }

    public String getComment() {
        return comment;
    }

    public void setComment(final String comment) {
        this.comment = comment;
    }

    public Integer getAlertDefinitionId() {
        return alertDefinitionId;
    }

    public void setAlertDefinitionId(final Integer alertDefinitionId) {
        this.alertDefinitionId = alertDefinitionId;
    }

    public String getEntityId() {
        return entityId;
    }

    public void setEntityId(final String entityId) {
        this.entityId = entityId;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("AlertComment [id=");
        builder.append(id);
        builder.append(", created=");
        builder.append(created);
        builder.append(", createdBy=");
        builder.append(createdBy);
        builder.append(", lastModified=");
        builder.append(lastModified);
        builder.append(", lastModifiedBy=");
        builder.append(lastModifiedBy);
        builder.append(", comment=");
        builder.append(comment);
        builder.append(", alertDefinitionId=");
        builder.append(alertDefinitionId);
        builder.append(", entityId=");
        builder.append(entityId);
        builder.append("]");
        return builder.toString();
    }

}
