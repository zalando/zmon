package de.zalando.zmon.appconfig;

/**
 * Created by jmussler on 10/21/14.
 */
public interface ZMonServiceConfig {

    public boolean isReadFromCassandraEnabled();

    public boolean writeToKairosDB();

    public boolean writeToCassandra();

    public boolean writeHistoryToCassandra();
}
