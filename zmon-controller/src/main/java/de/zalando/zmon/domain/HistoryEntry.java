package de.zalando.zmon.domain;

import java.util.Date;
import java.util.Map;

import de.zalando.typemapper.annotations.DatabaseField;

public class HistoryEntry {

    @DatabaseField
    private long id;

    @DatabaseField
    private Date timestamp;

    @DatabaseField
    private HistoryAction action;

    @DatabaseField
    private Map<String, String> rowData;

    @DatabaseField
    private Map<String, String> changedFields;

    @DatabaseField
    private String userName;

    @DatabaseField
    private int recordId;

    @DatabaseField
    private HistoryType historyType;

    public long getId() {
        return id;
    }

    public void setId(final long id) {
        this.id = id;
    }

    public Date getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(final Date timestamp) {
        this.timestamp = timestamp;
    }

    public HistoryAction getAction() {
        return action;
    }

    public void setAction(final HistoryAction action) {
        this.action = action;
    }

    public Map<String, String> getRowData() {
        return rowData;
    }

    public void setRowData(final Map<String, String> rowData) {
        this.rowData = rowData;
    }

    public Map<String, String> getChangedFields() {
        return changedFields;
    }

    public void setChangedFields(final Map<String, String> changedFields) {
        this.changedFields = changedFields;
    }

    public String getUserName() {
        return userName;
    }

    public void setUserName(final String userName) {
        this.userName = userName;
    }

    public int getRecordId() {
        return recordId;
    }

    public void setRecordId(final int recordId) {
        this.recordId = recordId;
    }

    public HistoryType getHistoryType() {
        return historyType;
    }

    public void setHistoryType(final HistoryType historyType) {
        this.historyType = historyType;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("HistoryEntry [id=");
        builder.append(id);
        builder.append(", timestamp=");
        builder.append(timestamp);
        builder.append(", action=");
        builder.append(action);
        builder.append(", rowData=");
        builder.append(rowData);
        builder.append(", changedFields=");
        builder.append(changedFields);
        builder.append(", userName=");
        builder.append(userName);
        builder.append(", recordId=");
        builder.append(recordId);
        builder.append(", historyType=");
        builder.append(historyType);
        builder.append("]");
        return builder.toString();
    }

}
