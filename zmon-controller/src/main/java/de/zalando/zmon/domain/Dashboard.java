package de.zalando.zmon.domain;

/**
 * @author  danieldelhoyo daniel.del.hoyo AT zalando DOT de
 */
import java.util.Date;
import java.util.List;

import javax.validation.constraints.NotNull;

import de.zalando.typemapper.annotations.DatabaseField;

public class Dashboard {

    @DatabaseField
    private Integer id;

    @DatabaseField
    @NotNull(message = "name is mandatory")
    private String name;

    @DatabaseField
    private String createdBy;

    @DatabaseField
    private Date lastModified;

    @DatabaseField
    private String lastModifiedBy;

    @DatabaseField
    @NotNull(message = "widget configuration is mandatory")
    private String widgetConfiguration;

    @DatabaseField
    private List<String> alertTeams;

    @DatabaseField
    @NotNull(message = "view mode is mandatory")
    private ViewMode viewMode;

    @DatabaseField
    @NotNull(message = "edit option is mandatory")
    private EditOption editOption;

    @DatabaseField
    private List<String> sharedTeams;

    @DatabaseField
    private List<String> tags;

    public Integer getId() {
        return id;
    }

    public void setId(final Integer id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(final String name) {
        this.name = name;
    }

    public String getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(final String createdBy) {
        this.createdBy = createdBy;
    }

    public Date getLastModified() {
        return lastModified;
    }

    public void setLastModified(final Date lastModified) {
        this.lastModified = lastModified;
    }

    public String getLastModifiedBy() {
        return lastModifiedBy;
    }

    public void setLastModifiedBy(final String lastModifiedBy) {
        this.lastModifiedBy = lastModifiedBy;
    }

    public String getWidgetConfiguration() {
        return widgetConfiguration;
    }

    public void setWidgetConfiguration(final String widgetConfiguration) {
        this.widgetConfiguration = widgetConfiguration;
    }

    public List<String> getAlertTeams() {
        return alertTeams;
    }

    public void setAlertTeams(final List<String> alertTeams) {
        this.alertTeams = alertTeams;
    }

    public ViewMode getViewMode() {
        return viewMode;
    }

    public void setViewMode(final ViewMode viewMode) {
        this.viewMode = viewMode;
    }

    public EditOption getEditOption() {
        return editOption;
    }

    public void setEditOption(final EditOption editOption) {
        this.editOption = editOption;
    }

    public List<String> getSharedTeams() {
        return sharedTeams;
    }

    public void setSharedTeams(final List<String> sharedTeams) {
        this.sharedTeams = sharedTeams;
    }

    public List<String> getTags() {
        return tags;
    }

    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("Dashboard{");
        sb.append("id=").append(id);
        sb.append(", name='").append(name).append('\'');
        sb.append(", createdBy='").append(createdBy).append('\'');
        sb.append(", lastModified=").append(lastModified);
        sb.append(", lastModifiedBy='").append(lastModifiedBy).append('\'');
        sb.append(", widgetConfiguration='").append(widgetConfiguration).append('\'');
        sb.append(", alertTeams=").append(alertTeams);
        sb.append(", viewMode=").append(viewMode);
        sb.append(", editOption=").append(editOption);
        sb.append(", sharedTeams=").append(sharedTeams);
        sb.append(", tags=").append(tags);
        sb.append('}');
        return sb.toString();
    }

    public void setTags(final List<String> tags) {
        this.tags = tags;
    }

}
