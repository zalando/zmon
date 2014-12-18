package de.zalando.zmon.exception;

public class AlertDefinitionFieldMissingException extends ZMonException {

    public static final ZMonExceptionFactory FACTORY = new ZMonExceptionFactory() {

        @Override
        public ZMonException create(final String message) {
            return new AlertDefinitionFieldMissingException(message);
        }
    };

    private static final long serialVersionUID = 1L;

    public AlertDefinitionFieldMissingException(final String message) {
        super(message);
    }
}
