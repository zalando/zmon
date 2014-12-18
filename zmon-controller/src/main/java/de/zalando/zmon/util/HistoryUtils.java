package de.zalando.zmon.util;

import java.util.Map;
import java.util.Set;

import com.google.common.collect.ImmutableSet;

/**
 * Created by pribeiro on 23/07/14.
 */
public final class HistoryUtils {

    private static final ImmutableSet<String> MODIFIED_BY_KEYS = ImmutableSet.of("adt_last_modified_by",
            "cd_last_modified_by");

    private static final ImmutableSet<String> NAME_KEYS = ImmutableSet.of("adt_name", "cd_name");

    private HistoryUtils() { }

    public static String resolveModifiedBy(final Map<String, String> attributes,
            final Map<String, String> changedAttributes) {
        return resolveParameterValue(attributes, changedAttributes, MODIFIED_BY_KEYS);
    }

    public static String resolveName(final Map<String, String> attributes,
            final Map<String, String> changedAttributes) {
        return resolveParameterValue(attributes, changedAttributes, NAME_KEYS);
    }

    public static String resolveParameterValue(final Map<String, String> attributes,
            final Map<String, String> changedAttributes, final Set<String> keys) {
        String value = getParameterValue(changedAttributes, keys);
        if (value != null) {
            return value;
        }

        value = getParameterValue(attributes, keys);
        if (value != null) {
            return value;
        }

        return null;
    }

    private static String getParameterValue(final Map<String, String> attributes, final Set<String> keys) {
        if (attributes != null && !attributes.isEmpty()) {
            for (final String key : keys) {
                final String value = attributes.get(key);
                if (key != null) {
                    return value;
                }
            }
        }

        return null;
    }
}
