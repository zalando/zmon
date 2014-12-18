package de.zalando.zmon.domain;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.fasterxml.jackson.databind.JsonNode;

public class CheckResults {

    private String entity;
    private List<JsonNode> results;
    private Set<Integer> activeAlertIds;

    public CheckResults() {

    }

    public CheckResults(String entity) {
        this.entity = entity;
        this.activeAlertIds = new HashSet<>();
        this.results = new ArrayList<>();
    }

    public String getEntity() {
        return entity;
    }

    public void setEntity(final String entity) {
        this.entity = entity;
    }

    public List<JsonNode> getResults() {
        return results;
    }

    public void setResults(final List<JsonNode> results) {
        this.results = results;
    }

    public Set<Integer> getActiveAlertIds() {
        return activeAlertIds;
    }

    public void setActiveAlertIds(final Set<Integer> activeAlertIds) {
        this.activeAlertIds = activeAlertIds;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("CheckResults [entity=");
        builder.append(entity);
        builder.append(", results=");
        builder.append(results);
        builder.append(", activeAlertIds=");
        builder.append(activeAlertIds);
        builder.append("]");
        return builder.toString();
    }
}
