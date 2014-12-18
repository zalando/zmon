package de.zalando.zmon.persistence;

import de.zalando.typemapper.annotations.DatabaseField;

import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.exception.ZMonExceptionFactory;

public class OperationResult {

    @DatabaseField
    private OperationStatus status;

    @DatabaseField
    private String errorMessage;

    public OperationStatus getStatus() {
        return status;
    }

    public void setStatus(final OperationStatus status) {
        this.status = status;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(final String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public <T extends OperationResult> T throwExceptionOnFailure() throws ZMonException {
        if (status != null) {
            final ZMonExceptionFactory factory = status.getExceptionFactory();
            if (factory != null) {
                throw factory.create(errorMessage);
            }
        }

        return (T) this;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("OperationResult [status=");
        builder.append(status);
        builder.append(", errorMessage=");
        builder.append(errorMessage);
        builder.append("]");
        return builder.toString();
    }

}
