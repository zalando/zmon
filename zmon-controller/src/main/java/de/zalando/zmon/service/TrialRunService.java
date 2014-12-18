package de.zalando.zmon.service;

import de.zalando.zmon.domain.TrialRunRequest;
import de.zalando.zmon.domain.TrialRunResults;

public interface TrialRunService {

    String scheduleTrialRun(TrialRunRequest request);

    TrialRunResults getTrialRunResults(String id);
}
