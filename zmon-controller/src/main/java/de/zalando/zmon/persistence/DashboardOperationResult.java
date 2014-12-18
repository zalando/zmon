package de.zalando.zmon.persistence;

import de.zalando.typemapper.annotations.DatabaseField;

import de.zalando.zmon.domain.Dashboard;

/**
 * @author  danieldelhoyo daniel.del.hoyo AT zalando DOT de
 */
public class DashboardOperationResult extends OperationResult {

    @DatabaseField
    private Dashboard entity;

    public Dashboard getEntity() {
        return entity;
    }

    public void setEntity(final Dashboard entity) {
        this.entity = entity;
    }
}
