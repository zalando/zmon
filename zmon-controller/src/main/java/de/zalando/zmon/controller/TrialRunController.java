package de.zalando.zmon.controller;

import java.util.Collections;
import java.util.Map;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

import de.zalando.zmon.domain.TrialRunRequest;
import de.zalando.zmon.domain.TrialRunResults;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.TrialRunService;

@Controller
public class TrialRunController extends AbstractZMonController {

    private static final String TRIAL_RUN_ID_KEY = "id";

    @Autowired
    private TrialRunService trialRunService;

    @Autowired
    private ZMonAuthorityService authorityService;

    @RequestMapping(value = "scheduleTrialRun", method = RequestMethod.POST)
    public ResponseEntity<Map<String, String>> scheduleTrial(
            @Valid
            @RequestBody(required = true)
            final TrialRunRequest request) {

        authorityService.verifyTrialRunPermission();
        request.setCreatedBy(authorityService.getUserName());

        return new ResponseEntity<>(Collections.singletonMap(TRIAL_RUN_ID_KEY,
                    trialRunService.scheduleTrialRun(request)), HttpStatus.OK);
    }

    @RequestMapping(value = "trialRunResults", method = RequestMethod.GET)
    public ResponseEntity<TrialRunResults> getTrialResults(
            @RequestParam(value = "id", required = true) final String id) {

        authorityService.verifyTrialRunPermission();

        final TrialRunResults results = trialRunService.getTrialRunResults(id);

        return results == null ? new ResponseEntity<TrialRunResults>(HttpStatus.NOT_FOUND)
                               : new ResponseEntity<>(results, HttpStatus.OK);
    }
}
