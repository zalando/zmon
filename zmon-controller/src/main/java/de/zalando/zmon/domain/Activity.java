package de.zalando.zmon.domain;

import java.util.Map;

public class Activity {

    private long time;
    private int typeId;
    private String typeName;
    private Map<String, String> attributes;

    public long getTime() {
        return time;
    }

    public void setTime(final long time) {
        this.time = time;
    }

    public int getTypeId() {
        return typeId;
    }

    public void setTypeId(final int typeId) {
        this.typeId = typeId;
    }

    public String getTypeName() {
        return typeName;
    }

    public void setTypeName(final String typeName) {
        this.typeName = typeName;
    }

    public Map<String, String> getAttributes() {
        return attributes;
    }

    public void setAttributes(final Map<String, String> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("Activity [time=");
        builder.append(time);
        builder.append(", typeId=");
        builder.append(typeId);
        builder.append(", typeName=");
        builder.append(typeName);
        builder.append(", attributes=");
        builder.append(attributes);
        builder.append("]");
        return builder.toString();
    }
}
