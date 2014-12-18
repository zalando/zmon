package de.zalando.zmon.rest;

import java.util.List;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.stereotype.Controller;

import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

import com.google.common.base.Preconditions;
import com.google.common.collect.Lists;

import de.zalando.zmon.controller.AbstractZMonController;
import de.zalando.zmon.domain.AlertDefinition;
import de.zalando.zmon.exception.CheckDefinitionNotActiveException;
import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.AlertService;

/**
 * Alert definitons REST API.
 *
 * <p/>Created by pribeiro on 26/08/14.
 */
@Controller
@RequestMapping("/api/v1/alert-definitions")
public class AlertDefinitionsApi extends AbstractZMonController {

    private final AlertService service;

    private final ZMonAuthorityService authorityService;

    @Autowired
    public AlertDefinitionsApi(final AlertService alertService, final ZMonAuthorityService authorityService) {
        this.service = Preconditions.checkNotNull(alertService, "alertService is null");
        this.authorityService = Preconditions.checkNotNull(authorityService, "authorityService is null");
    }

    @RequestMapping(method = RequestMethod.POST)
    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    public AlertDefinition create(@Valid
            @RequestBody(required = true)
            final AlertDefinition alertDefinition) throws ZMonException {
        alertDefinition.setId(null);
        alertDefinition.setLastModifiedBy(authorityService.getUserName());

        // check security
        authorityService.verifyEditAlertDefinitionPermission(alertDefinition);
        return service.createOrUpdateAlertDefinition(alertDefinition);
    }

    @RequestMapping(value = "/{id}", method = RequestMethod.PUT)
    public ResponseEntity<AlertDefinition> update(@PathVariable("id") final Integer id,
            @Valid
            @RequestBody(required = true)
            final AlertDefinition alertDefinition) throws ZMonException {
        alertDefinition.setId(id);
        alertDefinition.setLastModifiedBy(authorityService.getUserName());

        // check security
        authorityService.verifyEditAlertDefinitionPermission(alertDefinition);

        try {
            return new ResponseEntity<>(service.createOrUpdateAlertDefinition(alertDefinition), HttpStatus.OK);
        } catch (final CheckDefinitionNotActiveException e) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
    }

    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    public ResponseEntity<AlertDefinition> get(@PathVariable("id") final Integer id) {
        final List<AlertDefinition> alertDefinitions = service.getAlertDefinitions(null, Lists.newArrayList(id));
        if (alertDefinitions.isEmpty()) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }

        return new ResponseEntity<>(alertDefinitions.get(0), HttpStatus.OK);
    }

    @RequestMapping(value = "/{id}", method = RequestMethod.DELETE)
    public ResponseEntity<AlertDefinition> delete(@PathVariable("id") final Integer id) throws ZMonException {
        authorityService.verifyDeleteAlertDefinitionPermission(id);

        final AlertDefinition alertDefinition = service.deleteAlertDefinition(id);

        if (alertDefinition == null) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }

        return new ResponseEntity<>(alertDefinition, HttpStatus.OK);
    }
}
