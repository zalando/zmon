package de.zalando.zmon.domain;

import org.hamcrest.BaseMatcher;
import org.hamcrest.Description;
import org.hamcrest.Matcher;

import com.google.common.base.Objects;

public class ActivityIsEqual extends BaseMatcher<Activity> {

    private final Activity toImport;

    public ActivityIsEqual(final Activity toImport) {
        this.toImport = toImport;
    }

    public boolean matches(final Object o) {
        final Activity other = (Activity) o;

        return Objects.equal(toImport.getTime(), other.getTime())
                && Objects.equal(toImport.getTypeId(), other.getTypeId())
                && Objects.equal(toImport.getTypeName(), other.getTypeName())
                && Objects.equal(toImport.getAttributes(), other.getAttributes());

    }

    public void describeTo(final Description desc) {
        desc.appendText("time is ").appendValue(toImport.getTime()).appendText(", type id is ")
            .appendValue(toImport.getTypeId()).appendText(", type name is ").appendValue(toImport.getTypeName())
            .appendText(", attributes are ").appendValue(toImport.getAttributes());
    }

    // factory methods for fluent language
    public static Matcher<? super Activity> equalTo(final Activity activity) {
        return new ActivityIsEqual(activity);
    }
}
