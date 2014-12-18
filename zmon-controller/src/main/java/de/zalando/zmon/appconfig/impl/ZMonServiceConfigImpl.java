package de.zalando.zmon.appconfig.impl;

import de.zalando.zmon.appconfig.ZMonServiceConfig;
import org.springframework.stereotype.Service;

/**
 *
 * @author hjacobs
 */
@Service
public class ZMonServiceConfigImpl implements ZMonServiceConfig {

    @Override
    public boolean isReadFromCassandraEnabled() {
        return false;
    }

    @Override
    public boolean writeToKairosDB() {
        return false;
    }

    @Override
    public boolean writeToCassandra() {
        return false;
    }

    @Override
    public boolean writeHistoryToCassandra() {
        return false;
    }
    
}
