package de.zalando.zmon.exception;

public class ZMonException extends Exception {

    private static final long serialVersionUID = 2376965017029160488L;

    public ZMonException() {
        super();
    }

    public ZMonException(final String message) {
        super(message);
    }

    public ZMonException(final String message, final Throwable cause) {
        super(message, cause);
    }

    public ZMonException(final Throwable cause) {
        super(cause);
    }

}
