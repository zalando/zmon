package de.zalando.zmon.exception;

public interface ZMonExceptionFactory {

    ZMonException create(String message);
}
