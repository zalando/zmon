package de.zalando.zmon.domain;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlElementWrapper;

@XmlAccessorType(XmlAccessType.NONE)
public class AlertDefinitionsDiff {

    @XmlElement
    private Long snapshotId;

    @XmlElementWrapper(name = "disabledDefinitions")
    @XmlElement(name = "disabledDefinition")
    private List<Integer> disabledDefinitions;

    @XmlElementWrapper(name = "changedDefinitions")
    @XmlElement(name = "changedDefinition")
    private List<AlertDefinition> changedDefinitions;

    public Long getSnapshotId() {
        return snapshotId;
    }

    public void setSnapshotId(final Long snapshotId) {
        this.snapshotId = snapshotId;
    }

    public List<Integer> getDisabledDefinitions() {
        return disabledDefinitions;
    }

    public void setDisabledDefinitions(final List<Integer> disabledDefinitions) {
        this.disabledDefinitions = disabledDefinitions;
    }

    public List<AlertDefinition> getChangedDefinitions() {
        return changedDefinitions;
    }

    public void setChangedDefinitions(final List<AlertDefinition> changedDefinitions) {
        this.changedDefinitions = changedDefinitions;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("AlertDefinitionsDiff [snapshotId=");
        builder.append(snapshotId);
        builder.append(", disabledDefinitions=");
        builder.append(disabledDefinitions);
        builder.append(", changedDefinitions=");
        builder.append(changedDefinitions);
        builder.append("]");
        return builder.toString();
    }

}
