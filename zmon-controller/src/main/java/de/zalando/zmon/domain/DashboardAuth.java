package de.zalando.zmon.domain;

import org.springframework.beans.BeanUtils;

public class DashboardAuth extends Dashboard {

    private boolean editable;

    private boolean cloneable;

    private boolean editOptionEditable;

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

    public boolean isEditOptionEditable() {
        return editOptionEditable;
    }

    public void setEditOptionEditable(final boolean editOptionEditable) {
        this.editOptionEditable = editOptionEditable;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("DashboardAuth [editable=");
        builder.append(editable);
        builder.append(", cloneable=");
        builder.append(cloneable);
        builder.append(", editOptionEditable=");
        builder.append(editOptionEditable);
        builder.append("]");
        return builder.toString();
    }

    public static DashboardAuth from(final Dashboard dashboard, final boolean editable, final boolean cloneable,
            final boolean editOptionEditable) {

        DashboardAuth result = null;
        if (dashboard != null) {
            result = new DashboardAuth();

            BeanUtils.copyProperties(dashboard, result);
            result.setEditable(editable);
            result.setCloneable(cloneable);
            result.setEditOptionEditable(editOptionEditable);
        }

        return result;
    }

}
