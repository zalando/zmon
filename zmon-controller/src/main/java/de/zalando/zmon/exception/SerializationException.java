package de.zalando.zmon.exception;

public class SerializationException extends ZMonRuntimeException {

    private static final long serialVersionUID = -5145137507630370749L;

    public SerializationException(final String msg, final Throwable cause) {
        super(msg, cause);
    }

    public SerializationException(final String msg) {
        super(msg);
    }
}
