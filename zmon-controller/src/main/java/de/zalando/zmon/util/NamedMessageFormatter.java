package de.zalando.zmon.util;

import java.math.BigDecimal;

import java.util.Collection;
import java.util.LinkedList;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.base.Joiner;
import com.google.common.base.Preconditions;

public class NamedMessageFormatter {

    private static final Logger LOG = LoggerFactory.getLogger(NamedMessageFormatter.class);

    private static final Joiner COMMA_JOINER = Joiner.on(", ");

    private static final Pattern KEY_FORMAT_PATTERN = Pattern.compile(
            "\\{(?<key>[a-z_][a-z0-9-_]*)(:\\.(?<decimal>\\d+)f)?\\}", Pattern.CASE_INSENSITIVE);

    public String format(final String message, final Map<String, Collection<String>> values) {
        Preconditions.checkNotNull(message, "message");
        Preconditions.checkNotNull(values, "values");

        String result = message;
        if (!values.isEmpty()) {
            final Matcher keyFormat = KEY_FORMAT_PATTERN.matcher(message);
            if (keyFormat.find()) {
                final StringBuffer sb = new StringBuffer();
                do {
                    final String key = keyFormat.group("key");
                    final Collection<String> replacement = values.get(key);
                    if (replacement != null && !replacement.isEmpty()) {
                        final String decimalPlacesStr = keyFormat.group("decimal");
                        if (decimalPlacesStr == null) {
                            keyFormat.appendReplacement(sb, Matcher.quoteReplacement(COMMA_JOINER.join(replacement)));
                        } else {
                            final Collection<String> convertedValues = convertDecimalPlaces(message, key,
                                    decimalPlacesStr, replacement);
                            if (!convertedValues.isEmpty()) {
                                keyFormat.appendReplacement(sb,
                                    Matcher.quoteReplacement(COMMA_JOINER.join(convertedValues)));
                            }
                        }
                    }
                } while (keyFormat.find());

                result = keyFormat.appendTail(sb).toString();
            }
        }

        return result;
    }

    private Collection<String> convertDecimalPlaces(final String message, final String key,
            final String decimalPlacesStr, final Iterable<String> input) {
        final LinkedList<String> result = new LinkedList<>();
        try {
            final int scale = Integer.parseInt(decimalPlacesStr);
            for (final String s : input) {
                try {
                    result.add(new BigDecimal(s).setScale(scale, BigDecimal.ROUND_HALF_UP).toPlainString());
                } catch (final NumberFormatException e) {
                    LOG.debug("Could not parse number [{}] with key [{}]", s, key, e);
                }
            }
        } catch (final NumberFormatException e) {
            LOG.debug("Could not extract the number of decimal places [{}] from the named message [{}]",
                decimalPlacesStr, message, e);
        }

        return result;
    }
}
