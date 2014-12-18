package de.zalando.zmon.domain;

public class DowntimeDetails extends AbstractDowntime {

    private String id;

    private Integer alertDefinitionId;

    private String entity;

    private String groupId;

    public String getId() {
        return id;
    }

    public void setId(final String id) {
        this.id = id;
    }

    public Integer getAlertDefinitionId() {
        return alertDefinitionId;
    }

    public void setAlertDefinitionId(final Integer alertDefinitionId) {
        this.alertDefinitionId = alertDefinitionId;
    }

    public String getEntity() {
        return entity;
    }

    public void setEntity(final String entity) {
        this.entity = entity;
    }

    public String getGroupId() {
        return groupId;
    }

    public void setGroupId(final String groupId) {
        this.groupId = groupId;
    }

    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("DowntimeDetails{");
        sb.append("id='").append(id).append('\'');
        sb.append(", alertDefinitionId=").append(alertDefinitionId);
        sb.append(", entity='").append(entity).append('\'');
        sb.append(", groupId='").append(groupId).append('\'');
        sb.append('}');
        return sb.toString();
    }

}
