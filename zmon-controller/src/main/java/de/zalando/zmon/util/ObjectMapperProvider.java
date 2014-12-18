package de.zalando.zmon.util;

import org.springframework.beans.factory.FactoryBean;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategy;

public class ObjectMapperProvider implements FactoryBean<ObjectMapper> {

    // share object mapper with non managed spring instances
    public static final ObjectMapper OBJECT_MAPPER = createObjectMapper();

    private static ObjectMapper createObjectMapper() {
        return new ObjectMapper().setPropertyNamingStrategy(
                                     PropertyNamingStrategy.CAMEL_CASE_TO_LOWER_CASE_WITH_UNDERSCORES).configure(
                                     DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }

    @Override
    public ObjectMapper getObject() throws Exception {
        return OBJECT_MAPPER;
    }

    @Override
    public Class<ObjectMapper> getObjectType() {
        return ObjectMapper.class;
    }

    @Override
    public boolean isSingleton() {
        return true;
    }
}
