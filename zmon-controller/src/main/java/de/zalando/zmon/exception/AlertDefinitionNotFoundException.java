package de.zalando.zmon.exception;

public class AlertDefinitionNotFoundException extends ZMonException {

    public static final ZMonExceptionFactory FACTORY = new ZMonExceptionFactory() {

        @Override
        public ZMonException create(final String message) {
            return new AlertDefinitionNotFoundException(message);
        }
    };

    private static final long serialVersionUID = 1L;

    public AlertDefinitionNotFoundException(final String message) {
        super(message);
    }
}
