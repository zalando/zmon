package de.zalando.zmon.adapter;

import java.util.Map;

import javax.xml.bind.annotation.adapters.XmlAdapter;

import com.fasterxml.jackson.core.type.TypeReference;

import de.zalando.zmon.domain.Parameter;
import de.zalando.zmon.util.ObjectMapperProvider;

/**
 * Created by pribeiro on 24/06/14.
 */
public class JsonAdapter extends XmlAdapter<String, Map<String, Parameter>> {

    private static final TypeReference<Map<String, Parameter>> INPUT_TYPE =
        new TypeReference<Map<String, Parameter>>() { };

    @Override
    public Map<String, Parameter> unmarshal(final String v) throws Exception {
        if (v == null) {
            return null;
        }

        return ObjectMapperProvider.OBJECT_MAPPER.readValue(v, INPUT_TYPE);
    }

    @Override
    public String marshal(final Map<String, Parameter> v) throws Exception {
        if (v == null) {
            return null;
        }

        return ObjectMapperProvider.OBJECT_MAPPER.writeValueAsString(v);
    }
}
