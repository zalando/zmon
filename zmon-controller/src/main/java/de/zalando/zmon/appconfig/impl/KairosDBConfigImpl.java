package de.zalando.zmon.appconfig.impl;

import de.zalando.zmon.appconfig.KairosDBConfig;
import org.springframework.stereotype.Service;

/**
 *
 * @author hjacobs
 */
@Service
public class KairosDBConfigImpl implements KairosDBConfig {

    @Override
    public String getHost() {
        return null;
    }

    @Override
    public Integer getPort() {
        return null;
    }

    @Override
    public Boolean isEnabled() {
        return false;
    }
    
}
