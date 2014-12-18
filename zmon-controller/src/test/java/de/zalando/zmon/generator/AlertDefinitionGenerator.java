package de.zalando.zmon.generator;

import java.util.Collections;
import java.util.Date;
import java.util.Map;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.domain.Parameter;

public class AlertDefinitionGenerator implements DataGenerator<AlertDefinition> {

    @Override
    public AlertDefinition generate() {

        final AlertDefinition alertDefinition = new AlertDefinition();
        alertDefinition.setName("Generated alert definition name");
        alertDefinition.setDescription("Generated alert definition description");
        alertDefinition.setTeam("Platform/System");
        alertDefinition.setResponsibleTeam("Platform/Database");
        alertDefinition.setEntities(ImmutableList.<Map<String, String>>of(ImmutableMap.of("type", "zompy")));
        alertDefinition.setEntitiesExclude(ImmutableList.<Map<String, String>>of(ImmutableMap.of("type", "zomcat")));
        alertDefinition.setCondition(">=2");
        alertDefinition.setTemplate(false);
        alertDefinition.setNotifications(Collections.singletonList("EMAIL"));
        alertDefinition.setStatus(DefinitionStatus.ACTIVE);
        alertDefinition.setPriority(3);
        alertDefinition.setLastModified(new Date());
        alertDefinition.setLastModifiedBy("pribeiro");
        alertDefinition.setPeriod("");
        alertDefinition.setParameters(ImmutableMap.of("param_0", new Parameter(0, "desc 0", "int"), "param_1",
                new Parameter(1, "desc 1", "int")));
        alertDefinition.setTags(Collections.singletonList("DEV"));

        return alertDefinition;
    }

}
