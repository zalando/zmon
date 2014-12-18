package de.zalando.zmon.domain;

import javax.validation.constraints.NotNull;

/**
 * Created by pribeiro on 02/07/14.
 */
public class InstantaneousAlertEvaluationRequest {

    @NotNull(message = "alert definition id is mandatory")
    private Integer alertDefinitionId;

    public Integer getAlertDefinitionId() {
        return alertDefinitionId;
    }

    public void setAlertDefinitionId(final Integer alertDefinitionId) {
        this.alertDefinitionId = alertDefinitionId;
    }

    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("InstantaneousAlertEvaluationRequest{");
        sb.append("alertDefinitionId=").append(alertDefinitionId);
        sb.append('}');
        return sb.toString();
    }
}
