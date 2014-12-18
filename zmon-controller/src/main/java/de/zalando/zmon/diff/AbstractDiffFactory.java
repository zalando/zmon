package de.zalando.zmon.diff;

import java.util.LinkedList;
import java.util.List;

import de.zalando.zmon.domain.DefinitionStatus;

public abstract class AbstractDiffFactory<T, D extends StatusDiff> {

    public T create(final Long snapshotId, final List<D> definitions) {

        List<Integer> disabledDefinitions = null;
        List<D> changedDefinitions = null;

        if (definitions != null && !definitions.isEmpty()) {

            disabledDefinitions = new LinkedList<>();

            for (final D def : definitions) {

                if (DefinitionStatus.ACTIVE == def.getStatus()) {
                    if (changedDefinitions == null) {
                        changedDefinitions = new LinkedList<>();
                    }

                    changedDefinitions.add(def);
                } else {
                    disabledDefinitions.add(def.getId());
                }
            }
        }

        return create(snapshotId, disabledDefinitions, changedDefinitions);

    }

    protected abstract T create(final Long snapshotId, List<Integer> disabledDefinitions, List<D> changedDefinitions);

}
