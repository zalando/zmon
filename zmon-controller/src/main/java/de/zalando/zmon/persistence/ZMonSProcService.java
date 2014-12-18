package de.zalando.zmon.persistence;

import java.util.List;

import de.zalando.sprocwrapper.SProcCall;
import de.zalando.sprocwrapper.SProcService;

@SProcService
public interface ZMonSProcService {

    @SProcCall
    List<String> getAllTeams();
}
