package de.zalando.zmon.service;

import java.util.List;

import de.zalando.zmon.domain.Dashboard;
import de.zalando.zmon.exception.ZMonException;

public interface DashboardService {

    List<Dashboard> getDashboards(List<Integer> dashboardIds);

    List<Dashboard> getAllDashboards();

    Dashboard createOrUpdateDashboard(Dashboard dashboard) throws ZMonException;

    void deleteDashboard(Integer dashboardId);

}
