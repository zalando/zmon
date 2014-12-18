package de.zalando.zmon.appconfig;

import javax.annotation.Nonnull;

/**
 * Created by pribeiro on 21/07/14.
 */
public interface KairosDBConfig {

    @Nonnull
    String getHost();

    @Nonnull
    Integer getPort();

    @Nonnull
    Boolean isEnabled();
}
