package de.zalando.zmon.domain;

import com.google.common.base.Preconditions;

/**
 * Created by pribeiro on 17/07/14.
 */
public enum WorkerQueue {

    INTERNAL("zmon:queue:internal"),
    DEFAULT("zmon:queue:default"),
    SNMP("zmon:queue:snmp"),
    SECURE("zmon:queue:secure");

    private final String key;

    private WorkerQueue(final String key) {
        this.key = Preconditions.checkNotNull(key);
    }

    public String getKey() {
        return key;
    }
}
