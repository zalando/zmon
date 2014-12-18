package de.zalando.zmon.rest;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpStatus;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.InitBinder;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

import com.google.common.base.Preconditions;

import de.zalando.zmon.controller.AbstractZMonController;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.DowntimeService;
import de.zalando.zmon.validation.DowntimeValidator;

/**
 * Downtimes REST API. Created by pribeiro on 12/08/14.
 */
@Controller
@RequestMapping("/api/v1/downtimes")
public class DowntimesApi extends AbstractZMonController {

    private final DowntimeService downtimeService;
    private final ZMonAuthorityService authorityService;
    private final DowntimeValidator downtimeValidator;

    @InitBinder
    protected void initBinder(final WebDataBinder binder) {
        binder.setValidator(downtimeValidator);
    }

    @Autowired
    public DowntimesApi(final DowntimeService downtimeService, final ZMonAuthorityService authorityService,
            final DowntimeValidator downtimeValidator) {
        this.downtimeService = Preconditions.checkNotNull(downtimeService, "downtimeService");
        this.authorityService = Preconditions.checkNotNull(authorityService, "authorityService");
        this.downtimeValidator = Preconditions.checkNotNull(downtimeValidator, "downtimeValidator");
    }

    @RequestMapping(method = RequestMethod.POST)
    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    public DowntimeGroup create(@Valid
            @RequestBody(required = true)
            final DowntimeGroup request) {

        request.setCreatedBy(authorityService.getUserName());
        return downtimeService.scheduleDowntimeGroup(request);
    }

    @RequestMapping(value = "/{id}", method = RequestMethod.DELETE)
    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    public DowntimeGroup delete(@PathVariable("id") final String id) {
        return downtimeService.deleteDowntimeGroup(id);
    }
}
