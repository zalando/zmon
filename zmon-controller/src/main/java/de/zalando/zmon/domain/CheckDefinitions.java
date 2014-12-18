package de.zalando.zmon.domain;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;

import de.zalando.typemapper.annotations.DatabaseField;

@XmlAccessorType(XmlAccessType.NONE)
public class CheckDefinitions {

    @XmlElement
    @DatabaseField
    private Long snapshotId;

    @XmlElement
    @DatabaseField
    private List<CheckDefinition> checkDefinitions;

    public Long getSnapshotId() {
        return snapshotId;
    }

    public void setSnapshotId(final Long snapshotId) {
        this.snapshotId = snapshotId;
    }

    public List<CheckDefinition> getCheckDefinitions() {
        return checkDefinitions;
    }

    public void setCheckDefinitions(final List<CheckDefinition> checkDefinitions) {
        this.checkDefinitions = checkDefinitions;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("CheckDefinitions [snapshotId=");
        builder.append(snapshotId);
        builder.append(", checkDefinitions=");
        builder.append(checkDefinitions);
        builder.append("]");
        return builder.toString();
    }

}
