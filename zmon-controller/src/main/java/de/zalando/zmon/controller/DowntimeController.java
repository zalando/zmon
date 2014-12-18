package de.zalando.zmon.controller;

import java.util.List;
import java.util.Set;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.InitBinder;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import de.zalando.zmon.domain.DowntimeDetails;
import de.zalando.zmon.domain.DowntimeRequest;
import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.DowntimeService;
import de.zalando.zmon.validation.DowntimeValidator;

@Controller
public class DowntimeController extends AbstractZMonController {

    @Autowired
    private DowntimeService service;

    @Autowired
    private ZMonAuthorityService authorityService;

    @Autowired
    private DowntimeValidator downtimeValidator;

    @InitBinder
    protected void initBinder(final WebDataBinder binder) {
        binder.setValidator(downtimeValidator);
    }

    @RequestMapping(value = "scheduleDowntime", method = RequestMethod.POST)
    public ResponseEntity<List<String>> scheduleDowntime(
            @Valid
            @RequestBody(required = true)
            final DowntimeRequest request) throws ZMonException {

        authorityService.verifyScheduleDowntimePermission();
        request.setCreatedBy(authorityService.getUserName());

        return new ResponseEntity<>(service.scheduleDowntime(request), HttpStatus.OK);
    }

    @ResponseBody
    @RequestMapping(value = "deleteDowntimes", method = RequestMethod.DELETE)
    public void deleteDowntimes(@RequestParam(value = "downtime_id", required = true) final Set<String> downTimeIds)
        throws ZMonException {
        authorityService.verifyDeleteDowntimePermission();
        service.deleteDowntimes(downTimeIds);
    }

    @RequestMapping(value = "downtimes", method = RequestMethod.GET)
    public ResponseEntity<List<DowntimeDetails>> getDowntimes(
            @RequestParam(value = "alert_definition_id", required = false) final Set<Integer> alertDefinitionIds) {
        return new ResponseEntity<>(service.getDowntimes(alertDefinitionIds), HttpStatus.OK);
    }

}
