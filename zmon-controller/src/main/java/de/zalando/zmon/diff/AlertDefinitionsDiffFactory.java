package de.zalando.zmon.diff;

import java.util.List;

import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.AlertDefinitions;
import de.zalando.zmon.domain.AlertDefinitionsDiff;

public final class AlertDefinitionsDiffFactory extends AbstractDiffFactory<AlertDefinitionsDiff, AlertDefinition> {

    // cache instance since it's safe to use across multiple threads
    private static final AlertDefinitionsDiffFactory INSTANCE = new AlertDefinitionsDiffFactory();

    private AlertDefinitionsDiffFactory() { }

    @Override
    protected AlertDefinitionsDiff create(final Long snapshotId, final List<Integer> disabledDefinitions,
            final List<AlertDefinition> changedDefinitions) {

        final AlertDefinitionsDiff diff = new AlertDefinitionsDiff();
        diff.setSnapshotId(snapshotId);
        diff.setDisabledDefinitions(disabledDefinitions);
        diff.setChangedDefinitions(changedDefinitions);

        return diff;
    }

    public static AlertDefinitionsDiff create(final AlertDefinitions checkDefinitions) {
        Long snapshotId = null;
        List<AlertDefinition> definitions = null;

        if (checkDefinitions != null) {
            snapshotId = checkDefinitions.getSnapshotId();
            definitions = checkDefinitions.getAlertDefinitions();
        }

        return INSTANCE.create(snapshotId, definitions);
    }
}
