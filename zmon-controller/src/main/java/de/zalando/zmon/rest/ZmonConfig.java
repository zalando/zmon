package de.zalando.zmon.rest;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import de.zalando.zmon.appconfig.ZMonServiceConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * Created by jmussler on 11/18/14.
 */
@Controller
@RequestMapping("/api/v1/config")
public class ZmonConfig {

    private ZMonServiceConfig serviceConfig;

    private ObjectMapper mapper;

    @Autowired
    public ZmonConfig(ZMonServiceConfig c, ObjectMapper m) {
        serviceConfig = c;
        mapper = m;
    }

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/", method = RequestMethod.GET)
    public JsonNode getCurrent() {
        ObjectNode n = mapper.createObjectNode();

        n.put("writeToKairosDB", serviceConfig.writeToKairosDB());
        n.put("writeHistoryToCassandra", serviceConfig.writeHistoryToCassandra());
        n.put("writeToCassandra", serviceConfig.writeToCassandra());

        return n;
    }
}
