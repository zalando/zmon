package de.zalando.zmon.util;

import com.google.common.base.CharMatcher;

public final class DBUtil {

    public enum SqlLike {

        ANY_SEQUENCE("%"),
        ANY_SINGLE_CHARACTER("_"),
        DEFAULT_ESCAPE_CHARACTER("\\");

        private final String character;

        private SqlLike(final String delimiter) {
            this.character = delimiter;
        }

        public String getCharacter() {
            return character;
        }

        public static String concatAll() {
            final StringBuilder result = new StringBuilder();
            for (final SqlLike entry : SqlLike.values()) {
                result.append(entry.character);
            }

            return result.toString();
        }
    }

    private static final String SQL_LIKE_SPECIAL_CHARS = SqlLike.concatAll();

    private static final CharMatcher WILDCARD = CharMatcher.is('*');

    private DBUtil() { }

    public static String escapeSqlLike(final String input) {
        return prefix(input, CharMatcher.anyOf(SQL_LIKE_SPECIAL_CHARS), SqlLike.DEFAULT_ESCAPE_CHARACTER.character);
    }

    public static String expandExpression(final String input) {
        return WILDCARD.replaceFrom(DBUtil.escapeSqlLike(input), SqlLike.ANY_SEQUENCE.getCharacter());
    }

    public static String prefix(final String input) {
        return DBUtil.escapeSqlLike(input) + SqlLike.ANY_SEQUENCE.getCharacter();
    }

    private static String prefix(final CharSequence input, final CharMatcher matcher, final CharSequence prefix) {
        if (prefix.length() == 0) {
            return input.toString();
        }

        int pos = matcher.indexIn(input);
        if (pos == -1) {
            return input.toString();
        }

        final StringBuilder buf = new StringBuilder();

        int oldpos = 0;
        do {
            buf.append(input, oldpos, pos);
            buf.append(prefix);
            buf.append(input.charAt(pos));
            oldpos = pos + 1;
            pos = matcher.indexIn(input, oldpos);
        } while (pos != -1);

        buf.append(input, oldpos, input.length());

        return buf.toString();
    }
}
