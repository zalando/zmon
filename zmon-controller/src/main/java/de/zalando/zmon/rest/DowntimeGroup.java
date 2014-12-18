package de.zalando.zmon.rest;

import java.util.Set;

import javax.validation.Valid;

import org.hibernate.validator.constraints.NotEmpty;

import de.zalando.zmon.domain.AbstractDowntime;

/**
 * Created by pribeiro on 12/08/14.
 */
public class DowntimeGroup extends AbstractDowntime {

    private String id;

    @Valid
    @NotEmpty(message = "downtime request should have at least one entity")
    private Set<String> entities;

    @Valid
    private Set<Integer> alertDefinitions;

    public String getId() {
        return id;
    }

    public void setId(final String id) {
        this.id = id;
    }

    public Set<String> getEntities() {
        return entities;
    }

    public void setEntities(final Set<String> entities) {
        this.entities = entities;
    }

    public Set<Integer> getAlertDefinitions() {
        return alertDefinitions;
    }

    public void setAlertDefinitions(final Set<Integer> alertDefinitions) {
        this.alertDefinitions = alertDefinitions;
    }

    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("DowntimeGroup{");
        sb.append("id='").append(id).append('\'');
        sb.append(", entities=").append(entities);
        sb.append(", alertDefinitions=").append(alertDefinitions);
        sb.append('}');
        return sb.toString();
    }
}
