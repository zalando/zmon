package de.zalando.zmon.domain;

import java.util.Collection;
import java.util.LinkedList;
import java.util.List;

import org.hamcrest.BaseMatcher;
import org.hamcrest.Description;
import org.hamcrest.Matcher;

import com.google.common.base.Objects;
import com.google.common.base.Preconditions;

public class AlertDefinitionIsEqual extends BaseMatcher<AlertDefinition> {

    private final AlertDefinition alertDefinition;

    public AlertDefinitionIsEqual(final AlertDefinition alertDefinition) {
        this.alertDefinition = alertDefinition;
    }

    public boolean matches(final Object o) {
        final AlertDefinition other = (AlertDefinition) o;

        return Objects.equal(alertDefinition.getId(), other.getId())
                && Objects.equal(alertDefinition.getName(), other.getName())
                && Objects.equal(alertDefinition.getDescription(), other.getDescription())
                && Objects.equal(alertDefinition.getTeam(), other.getTeam())
                && Objects.equal(alertDefinition.getResponsibleTeam(), other.getResponsibleTeam())
                && Objects.equal(alertDefinition.getEntities(), other.getEntities())
                && Objects.equal(alertDefinition.getEntitiesExclude(), other.getEntitiesExclude())
                && Objects.equal(alertDefinition.getCondition(), other.getCondition())
                && Objects.equal(alertDefinition.getNotifications(), other.getNotifications())
                && Objects.equal(alertDefinition.getCheckDefinitionId(), other.getCheckDefinitionId())
                && Objects.equal(alertDefinition.getStatus(), other.getStatus())
                && Objects.equal(alertDefinition.getPriority(), other.getPriority())
                && Objects.equal(alertDefinition.getLastModified(), other.getLastModified())
                && Objects.equal(alertDefinition.getLastModifiedBy(), other.getLastModifiedBy())
                && Objects.equal(alertDefinition.getPeriod(), other.getPeriod())
                && Objects.equal(alertDefinition.getTemplate(), other.getTemplate())
                && Objects.equal(alertDefinition.getParentId(), other.getParentId())
                && Objects.equal(alertDefinition.getParameters(), other.getParameters())
                && Objects.equal(alertDefinition.getTags(), other.getTags());
    }

    @Override
    public void describeTo(final Description desc) {
        desc.appendText("{Id is ").appendValue(alertDefinition.getId()).appendText(", name is ")
            .appendValue(alertDefinition.getName()).appendText(", description is ")
            .appendValue(alertDefinition.getDescription()).appendText(", team is ")
            .appendValue(alertDefinition.getTeam()).appendText(", responsible team is ")
            .appendValue(alertDefinition.getResponsibleTeam()).appendText(", entities are ")
            .appendValue(alertDefinition.getEntities()).appendText(", exclude entities ")
            .appendValue(alertDefinition.getEntitiesExclude()).appendText(", condition is ")
            .appendValue(alertDefinition.getCondition()).appendText(", notifications are ")
            .appendValue(alertDefinition.getNotifications()).appendText(", check definition id is ")
            .appendValue(alertDefinition.getCheckDefinitionId()).appendText(", status is ")
            .appendValue(alertDefinition.getStatus()).appendText(", priority is ")
            .appendValue(alertDefinition.getPriority()).appendText(", last modified at ")
            .appendValue(alertDefinition.getLastModified()).appendText(", last modified by ")
            .appendValue(alertDefinition.getLastModifiedBy()).appendText(", period is ")
            .appendValue(alertDefinition.getPeriod()).appendText(", is template: ")
            .appendValue(alertDefinition.getTemplate()).appendText(", parent is ")
            .appendValue(alertDefinition.getParentId()).appendText(", parameters are ")
            .appendValue(alertDefinition.getParameters()).appendText(", tags are ")
            .appendValue(alertDefinition.getTags()).appendText("}");

    }

    // factory methods for fluent language
    public static Matcher<? super AlertDefinition> equalTo(final AlertDefinition alertDefinition) {
        Preconditions.checkNotNull(alertDefinition, "alertDefinition");
        return new AlertDefinitionIsEqual(alertDefinition);
    }

    public static Collection<Matcher<? super AlertDefinition>> equalTo(
            final Iterable<AlertDefinition> alertDefinitions) {
        Preconditions.checkNotNull(alertDefinitions, "alertDefinitions");

        final List<Matcher<? super AlertDefinition>> matchers = new LinkedList<>();
        for (final AlertDefinition alertDefinition : alertDefinitions) {
            matchers.add(new AlertDefinitionIsEqual(alertDefinition));
        }

        return matchers;
    }

}
