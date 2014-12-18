package de.zalando.zmon.transformer;

import java.io.IOException;

import java.util.Map;

import com.google.common.collect.ImmutableMap;

import de.zalando.typemapper.core.ValueTransformer;
import de.zalando.typemapper.postgres.HStore;

import de.zalando.zmon.domain.Parameter;
import de.zalando.zmon.exception.SerializationException;
import de.zalando.zmon.util.ObjectMapperProvider;

/**
 * Created by pribeiro on 24/06/14.
 */
public class JsonTransformer extends ValueTransformer<String, Map<String, Parameter>> {

    @Override
    public Map<String, Parameter> unmarshalFromDb(final String value) {
        if (value == null) {
            return null;
        }

        final HStore hstore = new HStore(value);
        final Map<String, String> map = hstore.asMap();

        final ImmutableMap.Builder<String, Parameter> builder = ImmutableMap.builder();
        for (final Map.Entry<String, String> entry : map.entrySet()) {
            try {
                builder.put(entry.getKey(),
                    ObjectMapperProvider.OBJECT_MAPPER.readValue(entry.getValue(), Parameter.class));
            } catch (final IOException e) {
                throw new SerializationException("Could not read JSON: " + entry.getValue(), e);
            }
        }

        return builder.build();
    }

    @Override
    public String marshalToDb(final Map<String, Parameter> input) {
        if (input == null) {
            return null;
        }

        final ImmutableMap.Builder<String, String> builder = ImmutableMap.builder();
        for (final Map.Entry<String, Parameter> entry : input.entrySet()) {
            try {
                builder.put(entry.getKey(), ObjectMapperProvider.OBJECT_MAPPER.writeValueAsString(entry.getValue()));
            } catch (final IOException e) {
                throw new SerializationException("Could serialize JSON: " + entry.getValue(), e);
            }
        }

        return HStore.serialize(builder.build());
    }
}
