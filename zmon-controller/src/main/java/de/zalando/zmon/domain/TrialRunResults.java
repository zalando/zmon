package de.zalando.zmon.domain;

import java.util.List;

import com.fasterxml.jackson.databind.JsonNode;

public class TrialRunResults {

    private int percentage;

    private List<JsonNode> results;

    public int getPercentage() {
        return percentage;
    }

    public void setPercentage(final int percentage) {
        this.percentage = percentage;
    }

    public List<JsonNode> getResults() {
        return results;
    }

    public void setResults(final List<JsonNode> results) {
        this.results = results;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("TrialRunResults [percentage=");
        builder.append(percentage);
        builder.append(", results=");
        builder.append(results);
        builder.append("]");
        return builder.toString();
    }
}
