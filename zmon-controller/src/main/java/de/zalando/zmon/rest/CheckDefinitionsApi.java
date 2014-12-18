package de.zalando.zmon.rest;

import com.google.common.base.Preconditions;
import de.zalando.zmon.controller.AbstractZMonController;
import de.zalando.zmon.domain.CheckDefinition;
import de.zalando.zmon.domain.CheckDefinitionImport;
import de.zalando.zmon.exception.ZMonException;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.ZMonService;
import javax.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

@Controller
@RequestMapping("/api/v1/check-definitions")
public class CheckDefinitionsApi extends AbstractZMonController {

    private final ZMonService zMonService;

    private final ZMonAuthorityService authorityService;

    @Autowired
    public CheckDefinitionsApi(final ZMonService zMonService, final ZMonAuthorityService authorityService) {
        this.zMonService = Preconditions.checkNotNull(zMonService, "zMonService is null");
        this.authorityService = Preconditions.checkNotNull(authorityService, "authorityService is null");
    }

    @RequestMapping(method = RequestMethod.POST)
    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    public CheckDefinition createOrUpdate(@Valid
            @RequestBody(required = true)
            final CheckDefinitionImport checkDefinition) throws ZMonException {

        return zMonService.createOrUpdateCheckDefinition(checkDefinition);
    }

}
