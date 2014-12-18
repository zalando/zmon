package de.zalando.zmon.domain;

import org.hamcrest.BaseMatcher;
import org.hamcrest.Description;
import org.hamcrest.Matcher;

import com.google.common.base.Objects;

public class AlertCommentIsEqual extends BaseMatcher<AlertComment> {

    private final AlertComment alertComment;

    public AlertCommentIsEqual(final AlertComment alertComment) {
        this.alertComment = alertComment;
    }

    @Override
    public boolean matches(final Object item) {
        final AlertComment other = (AlertComment) item;

        return Objects.equal(alertComment.getId(), other.getId())
                && Objects.equal(alertComment.getCreated(), other.getCreated())
                && Objects.equal(alertComment.getCreatedBy(), other.getCreatedBy())
                && Objects.equal(alertComment.getLastModified(), other.getLastModified())
                && Objects.equal(alertComment.getLastModifiedBy(), other.getLastModifiedBy())
                && Objects.equal(alertComment.getComment(), other.getComment())
                && Objects.equal(alertComment.getAlertDefinitionId(), other.getAlertDefinitionId())
                && Objects.equal(alertComment.getEntityId(), other.getEntityId());

    }

    @Override
    public void describeTo(final Description description) {
        description.appendText("{Id is ").appendValue(alertComment.getId()).appendText(", name is ")
                   .appendValue(alertComment.getCreated()).appendText(", created at ")
                   .appendValue(alertComment.getCreatedBy()).appendText(", created by ")
                   .appendValue(alertComment.getLastModified()).appendText(", modified at ")
                   .appendValue(alertComment.getLastModifiedBy()).appendText(", modified by ")
                   .appendValue(alertComment.getComment()).appendText(", comment is ")
                   .appendValue(alertComment.getAlertDefinitionId()).appendText(", alert definition id is ")
                   .appendValue(alertComment.getEntityId()).appendText(", entity id is ");
    }

    // factory methods for fluent language
    public static Matcher<? super AlertComment> equalTo(final AlertComment alertComment) {
        return new AlertCommentIsEqual(alertComment);
    }

}
