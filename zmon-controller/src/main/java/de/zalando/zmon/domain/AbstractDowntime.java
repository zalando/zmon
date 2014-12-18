package de.zalando.zmon.domain;

import java.util.concurrent.TimeUnit;

import javax.validation.constraints.NotNull;

public abstract class AbstractDowntime {

    @NotNull(message = "comment is mandatory")
    private String comment;

    @NotNull(message = "start time is mandatory")
    private Long startTime = TimeUnit.MILLISECONDS.toSeconds(System.currentTimeMillis());

    @NotNull(message = "end time is mandatory")
    private Long endTime;

    private String createdBy;

    public String getComment() {
        return comment;
    }

    public void setComment(final String comment) {
        this.comment = comment;
    }

    public Long getStartTime() {
        return startTime;
    }

    public void setStartTime(final Long startTime) {
        this.startTime = startTime;
    }

    public Long getEndTime() {
        return endTime;
    }

    public void setEndTime(final Long endTime) {
        this.endTime = endTime;
    }

    public String getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(final String createdBy) {
        this.createdBy = createdBy;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("AbstractDowntime [comment=");
        builder.append(comment);
        builder.append(", startTime=");
        builder.append(startTime);
        builder.append(", endTime=");
        builder.append(endTime);
        builder.append(", createdBy=");
        builder.append(createdBy);
        builder.append("]");
        return builder.toString();
    }

}
