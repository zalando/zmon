package de.zalando.zmon.generator;

import java.util.Map;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

import de.zalando.zmon.domain.CheckDefinitionImport;
import de.zalando.zmon.domain.DefinitionStatus;

public class CheckDefinitionImportGenerator implements DataGenerator<CheckDefinitionImport> {

    public CheckDefinitionImport generate() {

        final CheckDefinitionImport c = new CheckDefinitionImport();
        c.setName("Generated check definition name");
        c.setDescription("Generated check definition description");
        c.setTechnicalDetails("Generated technical details");
        c.setPotentialAnalysis("Generated potential analysis");
        c.setPotentialImpact("Generated potential impact");
        c.setPotentialSolution("Generated potential solution");
        c.setOwningTeam("Platform/Software");
        c.setEntities(ImmutableList.<Map<String, String>>of(ImmutableMap.of("type", "zomcat")));
        c.setInterval(10L);
        c.setCommand("zomcat().health()");
        c.setStatus(DefinitionStatus.ACTIVE);
        c.setSourceUrl(
            "https://scm.example.org/scm/platform/zmon2-software-checks.git/zmon-checks/zomcat-health.yaml");
        c.setLastModifiedBy("pribeiro");

        return c;
    }
}
