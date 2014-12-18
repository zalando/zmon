package de.zalando.zmon.domain;

import com.fasterxml.jackson.databind.JsonNode;

public class LastCheckResult {

    private final String entity;
    private final JsonNode result;

    public LastCheckResult(final String entity, final JsonNode result) {
        this.entity = entity;
        this.result = result;
    }

    public String getEntity() {
        return entity;
    }

    public JsonNode getResult() {
        return result;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("CheckResult [entity=");
        builder.append(entity);
        builder.append(", result=");
        builder.append(result);
        builder.append("]");
        return builder.toString();
    }

}
