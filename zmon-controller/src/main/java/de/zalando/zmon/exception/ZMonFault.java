package de.zalando.zmon.exception;

public class ZMonFault extends ZMonException {

    private static final long serialVersionUID = 1L;

    public ZMonFault(final String message) {
        super(message);
    }

    public ZMonFault(final String message, final Throwable cause) {
        super(message, cause);
    }

}
