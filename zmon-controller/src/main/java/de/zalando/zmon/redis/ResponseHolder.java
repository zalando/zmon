package de.zalando.zmon.redis;

import com.google.common.base.Preconditions;

import redis.clients.jedis.Response;

public final class ResponseHolder<K, R> {

    private final K key;
    private final Response<R> response;

    private ResponseHolder(final K key, final Response<R> response) {
        this.key = Preconditions.checkNotNull(key, "key");
        this.response = Preconditions.checkNotNull(response, "response");
    }

    public K getKey() {
        return key;
    }

    public Response<R> getResponse() {
        return response;
    }

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append("ResponseHolder [key=");
        builder.append(key);
        builder.append(", response=");
        builder.append(response);
        builder.append("]");
        return builder.toString();
    }

    public static <K, R> ResponseHolder<K, R> create(final K key, final Response<R> response) {
        return new ResponseHolder<>(key, response);
    }

}
