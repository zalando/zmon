package de.zalando.zmon.persistence;

import java.util.List;

import de.zalando.sprocwrapper.SProcCall;
import de.zalando.sprocwrapper.SProcParam;
import de.zalando.sprocwrapper.SProcService;

import de.zalando.zmon.domain.Dashboard;

@SProcService
public interface DashboardSProcService {

    @SProcCall
    List<Dashboard> getDashboards(@SProcParam List<Integer> dashboardIds);

    @SProcCall
    List<Dashboard> getAllDashboards();

    @SProcCall
    DashboardOperationResult createOrUpdateDashboard(@SProcParam Dashboard dashboard);

    @SProcCall
    void deleteDashboard(@SProcParam Integer dashboardId);

}
