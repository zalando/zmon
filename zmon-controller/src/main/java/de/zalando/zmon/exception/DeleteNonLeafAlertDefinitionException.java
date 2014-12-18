package de.zalando.zmon.exception;

public class DeleteNonLeafAlertDefinitionException extends ZMonException {

    public static final ZMonExceptionFactory FACTORY = new ZMonExceptionFactory() {

        @Override
        public ZMonException create(final String message) {
            return new DeleteNonLeafAlertDefinitionException(message);
        }
    };

    private static final long serialVersionUID = 1L;

    public DeleteNonLeafAlertDefinitionException(final String message) {
        super(message);
    }
}
