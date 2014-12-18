package de.zalando.zmon.validation;

import java.util.Collections;
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

import de.zalando.zmon.annotation.ContainsEntityKey;

public class ContainsEntityKeyValidatorTest {

    private static final class ContainsFilterKeyTest {

        @ContainsEntityKey(keys = {"type"})
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
        final ContainsFilterKeyTest test = new ContainsFilterKeyTest();

        final Set<ConstraintViolation<ContainsFilterKeyTest>> violations = validator.validate(test);
        Assert.assertEquals(1, violations.size());
    }

    @Test
    public void testNullEntity() {
        final ContainsFilterKeyTest test = new ContainsFilterKeyTest();
        test.entities = Collections.singletonList(null);

        final Set<ConstraintViolation<ContainsFilterKeyTest>> violations = validator.validate(test);
        Assert.assertEquals(1, violations.size());
    }

    @Test
    public void testEmptyFilter() {
        final ContainsFilterKeyTest test = new ContainsFilterKeyTest();
        test.entities = Collections.emptyList();

        final Set<ConstraintViolation<ContainsFilterKeyTest>> violations = validator.validate(test);
        Assert.assertEquals(1, violations.size());
    }

    @Test
    public void testEntitiesWithMandatoryKey() {
        final List<Map<String, String>> entities = new LinkedList<>();
        entities.add(ImmutableMap.of("type", "zomcat"));
        entities.add(ImmutableMap.of("type", "zompy"));

        final ContainsFilterKeyTest test = new ContainsFilterKeyTest();
        test.entities = entities;

        final Set<ConstraintViolation<ContainsFilterKeyTest>> violations = validator.validate(test);
        Assert.assertEquals(0, violations.size());
    }

    @Test
    public void testEntityWithMissingKey() {
        final List<Map<String, String>> entities = new LinkedList<>();
        entities.add(ImmutableMap.of("type", "zomcat"));
        entities.add(ImmutableMap.of("environment", "integration"));

        final ContainsFilterKeyTest test = new ContainsFilterKeyTest();
        test.entities = entities;

        final Set<ConstraintViolation<ContainsFilterKeyTest>> violations = validator.validate(test);
        Assert.assertEquals(1, violations.size());
    }

}
