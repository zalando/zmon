package de.zalando.zmon.domain;

public class HistoryReport extends ActivityDiff {

    private HistoryType historyType;

    public HistoryType getHistoryType() {
        return historyType;
    }

    public void setHistoryType(final HistoryType historyType) {
        this.historyType = historyType;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("HistoryReport [historyType=");
        builder.append(historyType);
        builder.append("]");
        return builder.toString();
    }

}
