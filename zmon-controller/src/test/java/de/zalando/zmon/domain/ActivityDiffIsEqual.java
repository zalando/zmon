package de.zalando.zmon.domain;

import org.hamcrest.BaseMatcher;
import org.hamcrest.Description;
import org.hamcrest.Matcher;

import com.google.common.base.Objects;

public class ActivityDiffIsEqual extends BaseMatcher<ActivityDiff> {

    private final ActivityDiff toImport;
    private final Matcher<? super Activity> activityMatcher;

    public ActivityDiffIsEqual(final ActivityDiff toImport) {
        this.toImport = toImport;
        this.activityMatcher = ActivityIsEqual.equalTo(toImport);
    }

    public boolean matches(final Object o) {
        final ActivityDiff other = (ActivityDiff) o;

        return activityMatcher.matches(other) && Objects.equal(toImport.getAction(), other.getAction())
                && Objects.equal(toImport.getChangedAttributes(), other.getChangedAttributes());
    }

    public void describeTo(final Description desc) {
        activityMatcher.describeTo(desc);
        desc.appendText("action is ").appendValue(toImport.getAction()).appendText(", changed attributes are ")
            .appendValue(toImport.getChangedAttributes());
    }

    // factory methods for fluent language
    public static Matcher<? super ActivityDiff> equalTo(final ActivityDiff activityDiff) {
        return new ActivityDiffIsEqual(activityDiff);
    }
}
