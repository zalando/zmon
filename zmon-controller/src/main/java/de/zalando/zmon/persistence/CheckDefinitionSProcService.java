package de.zalando.zmon.persistence;

import java.util.Date;
import java.util.List;

import de.zalando.sprocwrapper.SProcCall;
import de.zalando.sprocwrapper.SProcParam;
import de.zalando.sprocwrapper.SProcService;

import de.zalando.zmon.domain.CheckDefinition;
import de.zalando.zmon.domain.CheckDefinitionImport;
import de.zalando.zmon.domain.CheckDefinitions;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.domain.HistoryEntry;

@SProcService
public interface CheckDefinitionSProcService {

    @SProcCall
    List<CheckDefinition> getCheckDefinitions(@SProcParam DefinitionStatus status,
            @SProcParam List<Integer> checkDefinitionIds);

    @SProcCall
    List<CheckDefinition> getCheckDefinitionsByOwningTeam(@SProcParam DefinitionStatus status,
            @SProcParam List<String> owningTeams);

    @SProcCall
    CheckDefinitions getAllCheckDefinitions(@SProcParam DefinitionStatus status);

    @SProcCall
    CheckDefinitions getCheckDefinitionsDiff(@SProcParam Long lastSnapshotId);

    @SProcCall
    CheckDefinitionImportResult createOrUpdateCheckDefinition(@SProcParam CheckDefinitionImport checkDefinition);

    @SProcCall
    CheckDefinition deleteCheckDefinition(@SProcParam String userName, @SProcParam String name,
            @SProcParam String owningTeam);

    @SProcCall
    List<CheckDefinition> deleteDetachedCheckDefinitions();

    @SProcCall
    List<HistoryEntry> getCheckDefinitionHistory(@SProcParam int checkDefinitionId, @SProcParam int limit,
            @SProcParam Date from, @SProcParam Date to);
}
