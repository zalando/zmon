package de.zalando.zmon.domain;

import java.util.List;
import java.util.Map;

import javax.validation.Valid;
import javax.validation.constraints.Max;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;

import de.zalando.zmon.annotation.ContainsEntityKey;
import de.zalando.zmon.annotation.NotNullEntity;
import de.zalando.zmon.annotation.ParameterKey;

public class TrialRunRequest {

    private String id;

    @NotNull(message = "name is mandatory")
    private String name;

    @NotNull(message = "check command is mandatory")
    private String checkCommand;

    @NotNull(message = "alert condition is mandatory")
    private String alertCondition;

    @NotNull(message = "interval is mandatory")
    @Min(value = 1, message = "minimum interval value is 1")
    @Max(value = 3600, message = "maximum interval value for Trial Run is 3600")
    private Long interval;

    @NotNullEntity(message = "null filters not supported")
    @ContainsEntityKey(message = "each entity should contain field: type", keys = {"type"})
    private List<Map<String, String>> entities;

    @NotNullEntity(message = "null exclude filters not supported")
    private List<Map<String, String>> entitiesExclude;

    private String period;

    private String createdBy;

    @Valid
    @ParameterKey(message = "malformed parameter key")
    private Map<String, Parameter> parameters;

    public String getId() {
        return id;
    }

    public void setId(final String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(final String name) {
        this.name = name;
    }

    public String getCheckCommand() {
        return checkCommand;
    }

    public void setCheckCommand(final String checkCommand) {
        this.checkCommand = checkCommand;
    }

    public String getAlertCondition() {
        return alertCondition;
    }

    public void setAlertCondition(final String alertCondition) {
        this.alertCondition = alertCondition;
    }

    public Long getInterval() {
        return interval;
    }

    public void setInterval(final Long interval) {
        this.interval = interval;
    }

    public List<Map<String, String>> getEntities() {
        return entities;
    }

    public void setEntities(final List<Map<String, String>> entities) {
        this.entities = entities;
    }

    public List<Map<String, String>> getEntitiesExclude() {
        return entitiesExclude;
    }

    public void setEntitiesExclude(final List<Map<String, String>> entitiesExclude) {
        this.entitiesExclude = entitiesExclude;
    }

    public String getPeriod() {
        return period;
    }

    public void setPeriod(final String period) {
        this.period = period;
    }

    public String getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(final String createdBy) {
        this.createdBy = createdBy;
    }

    public Map<String, Parameter> getParameters() {
        return parameters;
    }

    public void setParameters(final Map<String, Parameter> parameters) {
        this.parameters = parameters;
    }

    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("TrialRunRequest{");
        sb.append("id='").append(id).append('\'');
        sb.append(", name='").append(name).append('\'');
        sb.append(", checkCommand='").append(checkCommand).append('\'');
        sb.append(", alertCondition='").append(alertCondition).append('\'');
        sb.append(", interval=").append(interval);
        sb.append(", entities=").append(entities);
        sb.append(", entitiesExclude=").append(entitiesExclude);
        sb.append(", period='").append(period).append('\'');
        sb.append(", createdBy='").append(createdBy).append('\'');
        sb.append(", parameters=").append(parameters);
        sb.append('}');
        return sb.toString();
    }

}
