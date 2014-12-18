package de.zalando.zmon.service.impl;

import java.util.List;

import org.hamcrest.MatcherAssert;
import org.hamcrest.Matchers;

import org.junit.Before;
import org.junit.Test;

import org.junit.runner.RunWith;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import org.springframework.transaction.annotation.Transactional;

import de.zalando.zmon.domain.ActivityDiff;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.domain.CheckDefinition;
import de.zalando.zmon.domain.CheckDefinitionImport;
import de.zalando.zmon.domain.HistoryReport;
import de.zalando.zmon.generator.AlertDefinitionGenerator;
import de.zalando.zmon.generator.CheckDefinitionImportGenerator;
import de.zalando.zmon.generator.DataGenerator;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = {"classpath:backendContextTest.xml"})
@Transactional
public class HistoryServiceImplIT {

    @Autowired
    private HistoryServiceImpl historyService;

    @Autowired
    @Qualifier("alert-service-redis")
    private AlertServiceImpl alertService;

    @Autowired
    @Qualifier("zmon-redis-service")
    private ZMonServiceImpl service;

    private DataGenerator<CheckDefinitionImport> checkImportGenerator;
    private DataGenerator<AlertDefinition> alertGenerator;

    @Before
    public void setup() {
        checkImportGenerator = new CheckDefinitionImportGenerator();
        alertGenerator = new AlertDefinitionGenerator();
    }

    @Test
    public void testGetCheckDefinitionHistory() throws Exception {

        final CheckDefinition newCheckDefinition = service.createOrUpdateCheckDefinition(
                checkImportGenerator.generate());

        // TODO test history pagination
        // TODO improve this test: check each field
        final List<ActivityDiff> history = historyService.getCheckDefinitionHistory(newCheckDefinition.getId(), 10,
                null, null);

        MatcherAssert.assertThat(history, Matchers.hasSize(1));
    }

    @Test
    public void testGetAlertDefinitionHistory() throws Exception {

        final CheckDefinition newCheckDefinition = service.createOrUpdateCheckDefinition(
                checkImportGenerator.generate());

        AlertDefinition newAlertDefinition = alertGenerator.generate();
        newAlertDefinition.setCheckDefinitionId(newCheckDefinition.getId());
        newAlertDefinition = alertService.createOrUpdateAlertDefinition(newAlertDefinition);

        // TODO test history pagination
        // TODO improve this test: check each field
        final List<ActivityDiff> history = historyService.getAlertDefinitionHistory(newAlertDefinition.getId(), 10,
                null, null);

        MatcherAssert.assertThat(history, Matchers.hasSize(1));
    }

    @Test
    public void testHistoryReportWithoutTimeRange() throws Exception {
        final CheckDefinitionImport toImport = checkImportGenerator.generate();
        toImport.setOwningTeam("Platform/Software");

        final CheckDefinition newCheckDefinition = service.createOrUpdateCheckDefinition(toImport);

        AlertDefinition newAlertDefinition = alertGenerator.generate();
        newAlertDefinition.setTeam("Platform/Database");
        newAlertDefinition.setResponsibleTeam("Platform/System");
        newAlertDefinition.setCheckDefinitionId(newCheckDefinition.getId());
        newAlertDefinition = alertService.createOrUpdateAlertDefinition(newAlertDefinition);

        final List<HistoryReport> history = historyService.getHistoryReport(newAlertDefinition.getTeam(),
                newAlertDefinition.getResponsibleTeam(), null, null);

        // TODO improve this test: check each field
        MatcherAssert.assertThat(history, Matchers.hasSize(2));
    }

    @Test
    public void testHistoryReportWithinTimeRange() throws Exception {
        final CheckDefinitionImport toImport = checkImportGenerator.generate();
        toImport.setOwningTeam("Platform/Software");

        final CheckDefinition newCheckDefinition = service.createOrUpdateCheckDefinition(toImport);

        AlertDefinition newAlertDefinition = alertGenerator.generate();
        newAlertDefinition.setTeam("Platform/Database");
        newAlertDefinition.setResponsibleTeam("Platform/System");
        newAlertDefinition.setCheckDefinitionId(newCheckDefinition.getId());
        newAlertDefinition = alertService.createOrUpdateAlertDefinition(newAlertDefinition);

        final long from = newAlertDefinition.getLastModified().getTime() / 1000;
        final long to = from + 1;

        final List<HistoryReport> history = historyService.getHistoryReport(newAlertDefinition.getTeam(),
                newAlertDefinition.getResponsibleTeam(), from, to);

        // TODO improve this test: check each field
        MatcherAssert.assertThat(history, Matchers.hasSize(2));
    }

    @Test
    public void testHistoryReportOutsideTimeRange() throws Exception {
        final CheckDefinitionImport toImport = checkImportGenerator.generate();
        toImport.setOwningTeam("Platform/Software");

        final CheckDefinition newCheckDefinition = service.createOrUpdateCheckDefinition(toImport);

        AlertDefinition newAlertDefinition = alertGenerator.generate();
        newAlertDefinition.setTeam("Platform/Database");
        newAlertDefinition.setResponsibleTeam("Platform/System");
        newAlertDefinition.setCheckDefinitionId(newCheckDefinition.getId());
        newAlertDefinition = alertService.createOrUpdateAlertDefinition(newAlertDefinition);

        final long from = newAlertDefinition.getLastModified().getTime() / 10000;
        final long to = from + 1;

        final List<HistoryReport> history = historyService.getHistoryReport(newAlertDefinition.getTeam(),
                newAlertDefinition.getResponsibleTeam(), from, to);

        // TODO improve this test: check each field
        MatcherAssert.assertThat(history, Matchers.hasSize(0));
    }

    @Test
    public void testHistoryReportWithoutTimeRangeAndNonExistingTeams() throws Exception {

        final CheckDefinitionImport toImport = checkImportGenerator.generate();
        final CheckDefinition newCheckDefinition = service.createOrUpdateCheckDefinition(toImport);

        AlertDefinition newAlertDefinition = alertGenerator.generate();
        newAlertDefinition.setCheckDefinitionId(newCheckDefinition.getId());
        newAlertDefinition = alertService.createOrUpdateAlertDefinition(newAlertDefinition);

        final List<HistoryReport> history = historyService.getHistoryReport("FOO" + newAlertDefinition.getTeam(),
                "BAR" + newAlertDefinition.getResponsibleTeam(), null, null);

        // TODO improve this test: check each field
        MatcherAssert.assertThat(history, Matchers.hasSize(0));
    }
}
