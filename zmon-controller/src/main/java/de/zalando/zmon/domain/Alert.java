package de.zalando.zmon.domain;

import java.util.List;

public class Alert {

    private AlertDefinitionAuth alertDefinition;
    private List<LastCheckResult> entities;
    private String message;

    public AlertDefinition getAlertDefinition() {
        return alertDefinition;
    }

    public void setAlertDefinition(final AlertDefinitionAuth alertDefinition) {
        this.alertDefinition = alertDefinition;
    }

    public List<LastCheckResult> getEntities() {
        return entities;
    }

    public void setEntities(final List<LastCheckResult> entities) {
        this.entities = entities;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(final String message) {
        this.message = message;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("AlertDetails [alertDefinition=");
        builder.append(alertDefinition);
        builder.append(", entities=");
        builder.append(entities);
        builder.append(", message=");
        builder.append(message);
        builder.append("]");
        return builder.toString();
    }

}
