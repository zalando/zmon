package de.zalando.zmon.utils;

import java.util.Collection;
import java.util.TreeMap;

import org.junit.Assert;
import org.junit.Test;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

import de.zalando.zmon.util.NamedMessageFormatter;

public class NamedMessageFormatterTest {

    private final NamedMessageFormatter messageFormatter = new NamedMessageFormatter();

    @Test
    public void testGroupReference() throws Exception {
        Assert.assertEquals(
            "CaMP Exceptions Overview last hour: de.zalando.angularjs.rpc.RPCMethodHandler$RPCInvocationTargetException: 35",
            messageFormatter.format("CaMP Exceptions Overview last hour: {problems}",
                ImmutableMap.<String, Collection<String>>of("problems",
                    ImmutableList.of("de.zalando.angularjs.rpc.RPCMethodHandler$RPCInvocationTargetException: 35"))));
    }

    @Test
    public void testWithoutPlaceholder() throws Exception {
        Assert.assertEquals("No Key",
            messageFormatter.format("No Key",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1.123123"))));
    }

    @Test
    public void testWithNonNumericValue() throws Exception {
        Assert.assertEquals("My value is value",
            messageFormatter.format("My value is {key}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("value"))));
    }

    @Test
    public void testWithoutKeyFormatting() throws Exception {
        Assert.assertEquals("My value is 1.123123",
            messageFormatter.format("My value is {key}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1.123123"))));
    }

    @Test
    public void testDecimalFormatWithNonNumericValue() throws Exception {
        Assert.assertEquals("My value is {key:.2f}",
            messageFormatter.format("My value is {key:.2f}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("value"))));
    }

    @Test
    public void test2DecimalPlaces() throws Exception {
        Assert.assertEquals("My value is 1.12",
            messageFormatter.format("My value is {key:.2f}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1.123123"))));
    }

    @Test
    public void testMultiplePlaceholders() {
        Assert.assertEquals("My value is 1.12 and 1.12",
            messageFormatter.format("My value is {key:.2f} and {key:.2f}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1.123123"))));
    }

    @Test
    public void testRounding() throws Exception {
        Assert.assertEquals("My value is 1.26",
            messageFormatter.format("My value is {key:.2f}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1.25555"))));

    }

    @Test
    public void testInteger() throws Exception {
        Assert.assertEquals("My value is 1.00",
            messageFormatter.format("My value is {key:.2f}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1"))));
    }

    @Test
    public void testMalformedBrackets() throws Exception {
        Assert.assertEquals("My value is {key:.2f",
            messageFormatter.format("My value is {key:.2f",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1"))));
    }

    @Test
    public void testMalformedNumber() throws Exception {
        Assert.assertEquals("My value is {key:.xf}",
            messageFormatter.format("My value is {key:.xf}",
                ImmutableMap.<String, Collection<String>>of("key", ImmutableList.of("1"))));
    }

    @Test
    public void testUpperCase() throws Exception {
        final TreeMap<String, Collection<String>> values = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        values.put("key", ImmutableList.of("1.123123"));

        Assert.assertEquals("MY VALUE IS 1.12 AND 1.12",
            messageFormatter.format("MY VALUE IS {KEY:.2F} AND {KEY:.2F}", values));
    }
}
