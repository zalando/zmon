package de.zalando.zmon.domain;

import java.util.List;

import javax.validation.Valid;

import org.hibernate.validator.constraints.NotEmpty;

public class DowntimeRequest extends AbstractDowntime {

    @Valid
    @NotEmpty(message = "downtime request should have at least one entity")
    private List<DowntimeEntities> downtimeEntities;

    public List<DowntimeEntities> getDowntimeEntities() {
        return downtimeEntities;
    }

    public void setDowntimeEntities(final List<DowntimeEntities> downtimeEntities) {
        this.downtimeEntities = downtimeEntities;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("Downtime [downtimeEntities=");
        builder.append(downtimeEntities);
        builder.append(", AbstractDowntime=");
        builder.append(super.toString());
        builder.append("]");
        return builder.toString();
    }

}
