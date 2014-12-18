package de.zalando.zmon.domain;

import java.util.Set;

import javax.validation.constraints.NotNull;

public class DowntimeEntities {

    @NotNull(message = "alert definition id is mandatory")
    private Integer alertDefinitionId;

    @NotNull(message = "downtime entity should have at least one entity id")
    private Set<String> entityIds;

    public Integer getAlertDefinitionId() {
        return alertDefinitionId;
    }

    public void setAlertDefinitionId(final Integer alertDefinitionId) {
        this.alertDefinitionId = alertDefinitionId;
    }

    public Set<String> getEntityIds() {
        return entityIds;
    }

    public void setEntityIds(final Set<String> entityIds) {
        this.entityIds = entityIds;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("DowntimeEntities [alertDefinitionId=");
        builder.append(alertDefinitionId);
        builder.append(", entityIds=");
        builder.append(entityIds);
        builder.append("]");
        return builder.toString();
    }

}
