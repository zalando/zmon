package de.zalando.zmon.domain;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlElementWrapper;

@XmlAccessorType(XmlAccessType.NONE)
public class Entity {

    @XmlElementWrapper(name = "attributes", required = true)
    @XmlElement(name = "attribute", required = true)
    private List<EntityAttribute> attributes;

    public List<EntityAttribute> getAttributes() {
        return attributes;
    }

    public void setAttributes(final List<EntityAttribute> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("Entity [attributes=");
        builder.append(attributes);
        builder.append("]");
        return builder.toString();
    }

}
