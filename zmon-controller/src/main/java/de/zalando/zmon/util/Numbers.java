package de.zalando.zmon.util;

import javax.annotation.Nonnull;

import com.google.common.base.Function;
import com.google.common.base.Preconditions;

public final class Numbers {

    private Numbers() { }

    public static final Function<String, Integer> PARSE_INTEGER_FUNCTION = new Function<String, Integer>() {

        @Override
        public Integer apply(@Nonnull final String input) {
            Preconditions.checkNotNull(input, "input");

            return Integer.valueOf(input);
        }
    };

}
