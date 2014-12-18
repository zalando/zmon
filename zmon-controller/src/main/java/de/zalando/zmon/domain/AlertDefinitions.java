package de.zalando.zmon.domain;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;

import de.zalando.typemapper.annotations.DatabaseField;

@XmlAccessorType(XmlAccessType.NONE)
public class AlertDefinitions {

    @XmlElement
    @DatabaseField
    private Long snapshotId;

    @XmlElement
    @DatabaseField
    private List<AlertDefinition> alertDefinitions;

    public Long getSnapshotId() {
        return snapshotId;
    }

    public void setSnapshotId(final Long snapshotId) {
        this.snapshotId = snapshotId;
    }

    public List<AlertDefinition> getAlertDefinitions() {
        return alertDefinitions;
    }

    public void setAlertDefinitions(final List<AlertDefinition> alertDefinitions) {
        this.alertDefinitions = alertDefinitions;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("AlertDefinitions [snapshotId=");
        builder.append(snapshotId);
        builder.append(", alertDefinitions=");
        builder.append(alertDefinitions);
        builder.append("]");
        return builder.toString();
    }

}
