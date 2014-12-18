package de.zalando.zmon.domain;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;

import com.google.common.base.Preconditions;

@XmlAccessorType(XmlAccessType.NONE)
public class EntityAttribute {

    @XmlElement(required = true)
    private String key;

    @XmlElement(required = true)
    private String value;

    public String getKey() {
        return key;
    }

    public void setKey(final String key) {
        this.key = key;
    }

    public String getValue() {
        return value;
    }

    public void setValue(final String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("EntityAttribute [key=");
        builder.append(key);
        builder.append(", value=");
        builder.append(value);
        builder.append("]");
        return builder.toString();
    }

    public static EntityAttribute from(final String key, final String value) {
        Preconditions.checkNotNull(key, "key");
        Preconditions.checkNotNull(value, "value");

        final EntityAttribute entity = new EntityAttribute();
        entity.setKey(key);
        entity.setValue(value);

        return entity;
    }

}
