package de.zalando.zmon.exception;

public class ZMonRuntimeException extends RuntimeException {

    private static final long serialVersionUID = -1211871300032776270L;

    public ZMonRuntimeException() {
        super();
    }

    public ZMonRuntimeException(final String message) {
        super(message);
    }

    public ZMonRuntimeException(final String message, final Throwable cause) {
        super(message, cause);
    }

    public ZMonRuntimeException(final Throwable cause) {
        super(cause);
    }

}
