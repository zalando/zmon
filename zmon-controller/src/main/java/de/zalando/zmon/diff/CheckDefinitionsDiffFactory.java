package de.zalando.zmon.diff;

import java.util.List;

import de.zalando.zmon.domain.CheckDefinition;
import de.zalando.zmon.domain.CheckDefinitions;
import de.zalando.zmon.domain.CheckDefinitionsDiff;

public final class CheckDefinitionsDiffFactory extends AbstractDiffFactory<CheckDefinitionsDiff, CheckDefinition> {

    // cache instance since it's safe to use across multiple threads
    private static final CheckDefinitionsDiffFactory INSTANCE = new CheckDefinitionsDiffFactory();

    private CheckDefinitionsDiffFactory() { }

    @Override
    protected CheckDefinitionsDiff create(final Long snapshotId, final List<Integer> disabledDefinitions,
            final List<CheckDefinition> changedDefinitions) {

        final CheckDefinitionsDiff diff = new CheckDefinitionsDiff();
        diff.setSnapshotId(snapshotId);
        diff.setDisabledDefinitions(disabledDefinitions);
        diff.setChangedDefinitions(changedDefinitions);

        return diff;
    }

    public static CheckDefinitionsDiff create(final CheckDefinitions checkDefinitions) {
        Long snapshotId = null;
        List<CheckDefinition> definitions = null;

        if (checkDefinitions != null) {
            snapshotId = checkDefinitions.getSnapshotId();
            definitions = checkDefinitions.getCheckDefinitions();
        }

        return INSTANCE.create(snapshotId, definitions);
    }
}
