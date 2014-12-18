package de.zalando.zmon.diff;

import de.zalando.zmon.domain.DefinitionStatus;

public interface StatusDiff {

    Integer getId();

    DefinitionStatus getStatus();

}
