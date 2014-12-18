package de.zalando.zmon.webservice.service;

import java.util.Set;

import javax.validation.ConstraintViolation;
import javax.validation.Validator;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

import de.zalando.zmon.domain.AlertDefinitions;
import de.zalando.zmon.domain.AlertDefinitionsDiff;
import de.zalando.zmon.domain.CheckDefinitionImport;
import de.zalando.zmon.domain.CheckDefinitions;
import de.zalando.zmon.domain.CheckDefinitionsDiff;
import de.zalando.zmon.domain.DefinitionStatus;
import de.zalando.zmon.exception.ZMonFault;
import de.zalando.zmon.service.AlertService;
import de.zalando.zmon.service.ZMonService;

// TODO check validation
// TODO handle errors
// TODO move interface to a new module
@Component(ZMonWebServiceImpl.BEAN_NAME)
public class ZMonWebServiceImpl implements ZMonWebService {

    public static final String BEAN_NAME = "zMonWebService";

    @Autowired
    private ZMonService zMonService;

    @Autowired
    private AlertService alertService;

    @Autowired
    private Validator validator;

    @Override
    public CheckDefinitions getAllCheckDefinitions() {
        return zMonService.getCheckDefinitions(null);
    }

    @Override
    public CheckDefinitions getAllActiveCheckDefinitions() {
        return zMonService.getCheckDefinitions(DefinitionStatus.ACTIVE);
    }

    @Override
    public CheckDefinitionsDiff getCheckDefinitionsDiff(final Long snapshotId) {
        return zMonService.getCheckDefinitionsDiff(snapshotId);
    }

    @Override
    public AlertDefinitions getAllActiveAlertDefinitions() {
        return alertService.getActiveAlertDefinitionsDiff();
    }

    @Override
    public AlertDefinitionsDiff getAlertDefinitionsDiff(final Long snapshotId) {
        return alertService.getAlertDefinitionsDiff(snapshotId);
    }

    @Override
    public void createOrUpdateCheckDefinition(final CheckDefinitionImport checkDefinition) throws ZMonFault {
        if (checkDefinition == null) {
            throw new ZMonFault("check definition is mandatory");
        }

        final Set<ConstraintViolation<CheckDefinitionImport>> results = validator.validate(checkDefinition);
        if (!results.isEmpty()) {
            throw new ZMonFault(results.iterator().next().getMessage());
        }

        zMonService.createOrUpdateCheckDefinition(checkDefinition);
    }

    @Override
    public void deleteCheckDefinition(final String name, final String owningTeam) throws ZMonFault {
        if (name == null) {
            throw new ZMonFault("name is mandatory");
        }

        if (owningTeam == null) {
            throw new ZMonFault("owning team is mandatory");
        }

        // TODO get user as parameter
        zMonService.deleteCheckDefinition("DISCOVERY", name, owningTeam);
    }

}
