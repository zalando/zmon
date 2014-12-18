package de.zalando.zmon.generator;

import java.util.Collections;

import de.zalando.zmon.domain.Dashboard;
import de.zalando.zmon.domain.EditOption;
import de.zalando.zmon.domain.ViewMode;

public class DashboardGenerator implements DataGenerator<Dashboard> {

    @Override
    public Dashboard generate() {

        final Dashboard dashboard = new Dashboard();
        dashboard.setName("Generated dashboard");
        dashboard.setCreatedBy("pribeiro");
        dashboard.setLastModifiedBy(dashboard.getCreatedBy());
        dashboard.setWidgetConfiguration(
            "[{\"type\": \"chart\", \"title\": \"ZMON Requests/s\", \"checkDefinitionId\": 202, \"entityId\": \"monitor03:3420\", \"options\": {\"colors\": [\"#0000FF\"]}}]");
        dashboard.setAlertTeams(Collections.singletonList("Platform/System"));
        dashboard.setViewMode(ViewMode.COMPACT);
        dashboard.setEditOption(EditOption.PRIVATE);
        dashboard.setSharedTeams(Collections.<String>emptyList());
        dashboard.setTags(Collections.singletonList("QA"));

        return dashboard;
    }

}
