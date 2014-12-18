package de.zalando.zmon.utils;

import org.hamcrest.MatcherAssert;
import org.hamcrest.Matchers;

import org.junit.Test;

import de.zalando.zmon.util.DBUtil;

public class DBUtilTest {

    @Test
    public void testEscapeSqlLike() {
        MatcherAssert.assertThat(DBUtil.escapeSqlLike("Platform_Software\\%"),
            Matchers.equalTo("Platform\\_Software\\\\\\%"));
    }

    @Test
    public void testExpandExpression() {
        MatcherAssert.assertThat(DBUtil.expandExpression("*Platfo*/_of%are*"),
            Matchers.equalTo("%Platfo%/\\_of\\%are%"));
    }

    @Test
    public void testPrefix() {
        MatcherAssert.assertThat(DBUtil.prefix("Platfo*/_of%are*"), Matchers.equalTo("Platfo*/\\_of\\%are*%"));
    }
}
