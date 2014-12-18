package de.zalando.zmon.adapter;

import java.util.Map;

import org.hamcrest.MatcherAssert;
import org.hamcrest.Matchers;

import org.junit.Test;

import org.junit.runner.RunWith;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import com.google.common.collect.ImmutableMap;

import de.zalando.zmon.domain.Parameter;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = {"classpath:backendContextTest.xml"})
public class JsonAdapterIT {

    @Autowired
    private ObjectMapper objectMapper;

    private final JsonAdapter jsonAdapter = new JsonAdapter();

    @Test
    public void testUnmarshalNull() throws Exception {
        MatcherAssert.assertThat(jsonAdapter.unmarshal(null), Matchers.nullValue());
    }

    @Test
    public void testUnmarshallJson() throws Exception {
        final JsonNode param0 = objectMapper.readTree("{\"value\":0,\"comment\":\"desc 0\",\"type\":\"int\"}");
        final JsonNode param1 = objectMapper.readTree("{\"value\":1,\"comment\":\"desc 1\",\"type\":\"float\"}");

        final ObjectNode node = objectMapper.createObjectNode();
        node.put("param0", param0);
        node.put("param1", param1);

        MatcherAssert.assertThat(jsonAdapter.unmarshal(node.toString()),
            Matchers.<Map<String, Parameter>>is(
                ImmutableMap.of("param0", new Parameter(0, "desc 0", "int"), "param1",
                    new Parameter(1, "desc 1", "float"))));
    }

    @Test
    public void testMarshallNull() throws Exception {
        MatcherAssert.assertThat(jsonAdapter.marshal(null), Matchers.nullValue());
    }

    @Test
    public void testMarshallJson() throws Exception {

        final ImmutableMap<String, Parameter> input = ImmutableMap.of("param0", new Parameter(0, "desc 0", "int"),
                "param1", new Parameter(1, "desc 1", "float"));

        final ObjectNode node = objectMapper.createObjectNode();
        node.put("param0", objectMapper.readTree("{\"value\":0,\"comment\":\"desc 0\",\"type\":\"int\"}"));
        node.put("param1", objectMapper.readTree("{\"value\":1,\"comment\":\"desc 1\",\"type\":\"float\"}"));

        MatcherAssert.assertThat(jsonAdapter.marshal(input), Matchers.is(node.toString()));
    }
}
