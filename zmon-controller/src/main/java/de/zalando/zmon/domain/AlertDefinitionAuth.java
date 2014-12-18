package de.zalando.zmon.domain;

import org.springframework.beans.BeanUtils;

public class AlertDefinitionAuth extends AlertDefinition {

    private boolean editable;

    private boolean cloneable;

    private boolean deletable;

    public boolean isEditable() {
        return editable;
    }

    public void setEditable(final boolean editable) {
        this.editable = editable;
    }

    public boolean isCloneable() {
        return cloneable;
    }

    public void setCloneable(final boolean cloneable) {
        this.cloneable = cloneable;
    }

    public boolean isDeletable() {
        return deletable;
    }

    public void setDeletable(final boolean deletable) {
        this.deletable = deletable;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("AlertDefinitionAuth [editable=");
        builder.append(editable);
        builder.append(", cloneable=");
        builder.append(cloneable);
        builder.append(", deletable=");
        builder.append(deletable);
        builder.append(", AlertDefinition=");
        builder.append(super.toString());
        builder.append("]");
        return builder.toString();
    }

    public static AlertDefinitionAuth from(final AlertDefinition alertDefinition, final boolean editable,
            final boolean cloneable, final boolean deletable) {

        AlertDefinitionAuth result = null;
        if (alertDefinition != null) {
            result = new AlertDefinitionAuth();

            BeanUtils.copyProperties(alertDefinition, result);
            result.setEditable(editable);
            result.setCloneable(cloneable);
            result.setDeletable(deletable);
        }

        return result;
    }

}
