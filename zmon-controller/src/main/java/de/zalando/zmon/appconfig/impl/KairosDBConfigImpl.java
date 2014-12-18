package de.zalando.zmon.appconfig.impl;

import de.zalando.zmon.appconfig.KairosDBConfig;
import org.springframework.stereotype.Service;

/**
 * FIXME: hardcoded config for Vagrant box
 * 
 * @author hjacobs
 */
@Service
public class KairosDBConfigImpl implements KairosDBConfig {

    @Override
    public String getHost() {
        return "localhost";
    }

    @Override
    public Integer getPort() {
        return 8083;
    }

    @Override
    public Boolean isEnabled() {
        return true;
    }
    
}
