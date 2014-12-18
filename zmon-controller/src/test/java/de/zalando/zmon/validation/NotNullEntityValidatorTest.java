package de.zalando.zmon.validation;

import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.validation.ConstraintViolation;
import javax.validation.Validation;
import javax.validation.Validator;
import javax.validation.ValidatorFactory;

import org.junit.Assert;
import org.junit.BeforeClass;
import org.junit.Test;

import com.google.common.collect.ImmutableMap;

import de.zalando.zmon.annotation.NotNullEntity;

public class NotNullEntityValidatorTest {

    private static final class NotNullFilterTest {

        @NotNullEntity
        private List<Map<String, String>> entities;
    }

    private static Validator validator;

    @BeforeClass
    public static void setup() {
        final ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
        validator = factory.getValidator();
    }

    @Test
    public void testNullFilter() {
        final NotNullFilterTest test = new NotNullFilterTest();

        final Set<ConstraintViolation<NotNullFilterTest>> violations = validator.validate(test);
        Assert.assertEquals(0, violations.size());
    }

    @Test
    public void testNullEntity() {
        final NotNullFilterTest test = new NotNullFilterTest();
        test.entities = Collections.singletonList(null);

        final Set<ConstraintViolation<NotNullFilterTest>> violations = validator.validate(test);
        Assert.assertEquals(1, violations.size());
    }

    @Test
    public void testEmptyFilter() {
        final NotNullFilterTest test = new NotNullFilterTest();
        test.entities = Collections.emptyList();

        final Set<ConstraintViolation<NotNullFilterTest>> violations = validator.validate(test);
        Assert.assertEquals(0, violations.size());
    }

    @Test
    public void testNotNullEntities() {
        final List<Map<String, String>> entities = new LinkedList<>();
        entities.add(ImmutableMap.of("type", "zomcat"));
        entities.add(ImmutableMap.of("type", "zompy"));

        final NotNullFilterTest test = new NotNullFilterTest();
        test.entities = entities;

        final Set<ConstraintViolation<NotNullFilterTest>> violations = validator.validate(test);
        Assert.assertEquals(0, violations.size());
    }

    @Test
    public void testEntityWithNullValue() {
        final List<Map<String, String>> entities = new LinkedList<>();
        entities.add(ImmutableMap.of("type", "zomcat"));

        final Map<String, String> filter = new HashMap<>();
        filter.put("type", null);
        entities.add(filter);

        final NotNullFilterTest test = new NotNullFilterTest();
        test.entities = entities;

        final Set<ConstraintViolation<NotNullFilterTest>> violations = validator.validate(test);
        Assert.assertEquals(1, violations.size());
    }

    @Test
    public void testEntityWithNullKey() {
        final List<Map<String, String>> entities = new LinkedList<>();
        entities.add(ImmutableMap.of("type", "zomcat"));

        final Map<String, String> filter = new HashMap<>();
        filter.put(null, "zompy");
        entities.add(filter);

        final NotNullFilterTest test = new NotNullFilterTest();
        test.entities = entities;

        final Set<ConstraintViolation<NotNullFilterTest>> violations = validator.validate(test);
        Assert.assertEquals(1, violations.size());
    }

}
