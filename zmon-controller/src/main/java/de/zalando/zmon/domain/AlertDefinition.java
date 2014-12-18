package de.zalando.zmon.domain;

import java.util.Date;
import java.util.List;
import java.util.Map;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlElementWrapper;
import javax.xml.bind.annotation.adapters.XmlJavaTypeAdapter;

import de.zalando.typemapper.annotations.DatabaseField;
import de.zalando.typemapper.annotations.DatabaseType;

import de.zalando.zmon.adapter.EntityListAdapter;
import de.zalando.zmon.adapter.JsonAdapter;
import de.zalando.zmon.annotation.NotNullEntity;
import de.zalando.zmon.annotation.ParameterKey;
import de.zalando.zmon.diff.StatusDiff;
import de.zalando.zmon.transformer.JsonTransformer;

// TODO check condition encoding
// TODO replace interval by something with time ranges
// TODO move interfaces to a new module (webservice)

@XmlAccessorType(XmlAccessType.NONE)
@DatabaseType(name = "alert_definition_type")
public class AlertDefinition implements StatusDiff {

    @XmlElement(required = true)
    @DatabaseField
    private Integer id;

    @XmlElement(required = true)
    @DatabaseField
    private String name;

    @XmlElement(required = true)
    @DatabaseField
    private String description;

    @XmlElement(required = true)
    @DatabaseField
    @NotNull(message = "team is mandatory")
    private String team;

    @XmlElement(required = true)
    @DatabaseField
    @NotNull(message = "responsible team is mandatory")
    private String responsibleTeam;

    /* Map passing
     * JAXB also doesn't support Maps.  It handles Lists great, but Maps are
     * not supported directly. Use of a XmlAdapter to map the maps into beans that JAXB can use.
     */
    @XmlJavaTypeAdapter(EntityListAdapter.class)
    @DatabaseField
    @NotNullEntity(message = "null filters not supported")
    private List<Map<String, String>> entities;

    @XmlJavaTypeAdapter(EntityListAdapter.class)
    @DatabaseField
    @NotNullEntity(message = "null filters not supported")
    private List<Map<String, String>> entitiesExclude;

    @XmlElement(required = true)
    @DatabaseField
    private String condition;

    @XmlElementWrapper(name = "notifications")
    @XmlElement(name = "notification")
    @DatabaseField
    private List<String> notifications;

    @XmlElement(required = true)
    @DatabaseField
    private Integer checkDefinitionId;

    @XmlElement(required = true)
    @DatabaseField
    @NotNull(message = "status is mandatory")
    private DefinitionStatus status;

    @XmlElement(required = true)
    @DatabaseField
    private Integer priority;

    @DatabaseField
    private Date lastModified;

    @DatabaseField
    private String lastModifiedBy;

    @XmlElement
    @DatabaseField
    private String period;

    @DatabaseField
    @NotNull(message = "template is mandatory")
    private Boolean template;

    @DatabaseField
    private Integer parentId;

    @Valid
    @XmlJavaTypeAdapter(JsonAdapter.class)
    @DatabaseField(transformer = JsonTransformer.class)
    @ParameterKey(message = "Malformed alert parameter key")
    private Map<String, Parameter> parameters;

    @DatabaseField
    private List<String> tags;

    public Integer getId() {
        return id;
    }

    public void setId(final Integer id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(final String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(final String description) {
        this.description = description;
    }

    public String getTeam() {
        return team;
    }

    public void setTeam(final String team) {
        this.team = team;
    }

    public String getResponsibleTeam() {
        return responsibleTeam;
    }

    public void setResponsibleTeam(final String responsibleTeam) {
        this.responsibleTeam = responsibleTeam;
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

    public String getCondition() {
        return condition;
    }

    public void setCondition(final String condition) {
        this.condition = condition;
    }

    public List<String> getNotifications() {
        return notifications;
    }

    public void setNotifications(final List<String> notifications) {
        this.notifications = notifications;
    }

    public Integer getCheckDefinitionId() {
        return checkDefinitionId;
    }

    public void setCheckDefinitionId(final Integer checkDefinitionId) {
        this.checkDefinitionId = checkDefinitionId;
    }

    public DefinitionStatus getStatus() {
        return status;
    }

    public void setStatus(final DefinitionStatus status) {
        this.status = status;
    }

    public Integer getPriority() {
        return priority;
    }

    public void setPriority(final Integer priority) {
        this.priority = priority;
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

    public String getPeriod() {
        return period;
    }

    public void setPeriod(final String period) {
        this.period = period;
    }

    public Boolean getTemplate() {
        return template;
    }

    public void setTemplate(final Boolean template) {
        this.template = template;
    }

    public Integer getParentId() {
        return parentId;
    }

    public void setParentId(final Integer parentId) {
        this.parentId = parentId;
    }

    public Map<String, Parameter> getParameters() {
        return parameters;
    }

    public void setParameters(final Map<String, Parameter> parameters) {
        this.parameters = parameters;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(final List<String> tags) {
        this.tags = tags;
    }

    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("AlertDefinition{");
        sb.append("id=").append(id);
        sb.append(", name='").append(name).append('\'');
        sb.append(", description='").append(description).append('\'');
        sb.append(", team='").append(team).append('\'');
        sb.append(", responsibleTeam='").append(responsibleTeam).append('\'');
        sb.append(", entities=").append(entities);
        sb.append(", entitiesExclude=").append(entitiesExclude);
        sb.append(", condition='").append(condition).append('\'');
        sb.append(", notifications=").append(notifications);
        sb.append(", checkDefinitionId=").append(checkDefinitionId);
        sb.append(", status=").append(status);
        sb.append(", priority=").append(priority);
        sb.append(", lastModified=").append(lastModified);
        sb.append(", lastModifiedBy='").append(lastModifiedBy).append('\'');
        sb.append(", period='").append(period).append('\'');
        sb.append(", template=").append(template);
        sb.append(", parentId=").append(parentId);
        sb.append(", parameters=").append(parameters);
        sb.append(", tags=").append(tags);
        sb.append('}');
        return sb.toString();
    }
}
