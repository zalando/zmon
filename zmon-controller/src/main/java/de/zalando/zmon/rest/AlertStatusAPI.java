package de.zalando.zmon.rest;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ContainerNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import de.zalando.zmon.redis.ResponseHolder;
import de.zalando.zmon.service.AlertService;
import de.zalando.zmon.service.ZMonService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.Pipeline;

import java.io.IOException;
import java.util.*;

/**
 * Created by jmussler on 11/17/14.
 */
@Controller
@RequestMapping("/api/v1/status")
public class AlertStatusAPI {

    private final JedisPool jedisPool;
    protected ObjectMapper mapper;

    private static final Logger LOG = LoggerFactory.getLogger(AlertStatusAPI.class);

    @Autowired
    public AlertStatusAPI(final JedisPool p, final ObjectMapper m) {
        jedisPool = p;
        mapper = m;
    }

    /*
    * {<id>: { entity: value } }
    *
    **/

    @ResponseStatus(HttpStatus.OK)
    @ResponseBody
    @RequestMapping(value = "/alert/{ids}/", method = RequestMethod.GET)
    public JsonNode getAlertStatus(@PathVariable("ids") final List<String> ids) throws IOException {
        Jedis jedis = jedisPool.getResource();

        Map<String, List<ResponseHolder<String,String>>> results = new HashMap<>();
        for(String id : ids) {
            results.put(id, new ArrayList<ResponseHolder<String,String>>());
        }

        try {
            List<ResponseHolder<String, Set<String>>> responses = new ArrayList<>();
            {
                Pipeline p = jedis.pipelined();
                for (String id : ids) {
                    responses.add(ResponseHolder.create(id, p.smembers("zmon:alerts:" + id)));
                }
                p.sync();
            }

            {
                Pipeline p = jedis.pipelined();
                for(ResponseHolder<String,Set<String>> r : responses) {
                    for( String m : r.getResponse().get() ) {
                        results.get(r.getKey()).add(ResponseHolder.create(m,p.get("zmon:alerts:" + r.getKey() + ":" + m)));
                    }
                }
                p.sync();
            }
        }
        finally {
            jedisPool.returnResource(jedis);
        }

        ObjectNode resultNode = mapper.createObjectNode();

        for(String id : ids) {
            List<ResponseHolder<String,String>> lr = results.get(id);
            ObjectNode entities = mapper.createObjectNode();
            for( ResponseHolder<String, String> rh : lr ) {
                entities.put(rh.getKey(), mapper.readTree(rh.getResponse().get()));
            }
            if(lr.size()>0) {
                resultNode.put(id, entities);
            }
        }

        return resultNode;
    }
}
