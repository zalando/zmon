package de.zalando.zmon.exception;

public class CheckDefinitionNotActiveException extends ZMonException {

    public static final ZMonExceptionFactory FACTORY = new ZMonExceptionFactory() {

        @Override
        public ZMonException create(final String message) {
            return new CheckDefinitionNotActiveException(message);
        }
    };

    private static final long serialVersionUID = 1L;

    public CheckDefinitionNotActiveException(final String message) {
        super(message);
    }
}
