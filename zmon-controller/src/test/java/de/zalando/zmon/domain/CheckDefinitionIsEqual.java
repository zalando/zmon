package de.zalando.zmon.domain;

import java.util.Collection;
import java.util.LinkedList;
import java.util.List;

import org.hamcrest.BaseMatcher;
import org.hamcrest.Description;
import org.hamcrest.Matcher;

import com.google.common.base.Objects;
import com.google.common.base.Preconditions;

public class CheckDefinitionIsEqual extends BaseMatcher<CheckDefinition> {

    private final CheckDefinition checkDefinition;

    public CheckDefinitionIsEqual(final CheckDefinition checkDefinition) {
        this.checkDefinition = checkDefinition;
    }

    public boolean matches(final Object o) {
        final CheckDefinition other = (CheckDefinition) o;

        return Objects.equal(checkDefinition.getId(), other.getId())
                && Objects.equal(checkDefinition.getName(), other.getName())
                && Objects.equal(checkDefinition.getDescription(), other.getDescription())
                && Objects.equal(checkDefinition.getTechnicalDetails(), other.getTechnicalDetails())
                && Objects.equal(checkDefinition.getPotentialAnalysis(), other.getPotentialAnalysis())
                && Objects.equal(checkDefinition.getPotentialImpact(), other.getPotentialImpact())
                && Objects.equal(checkDefinition.getPotentialSolution(), other.getPotentialSolution())
                && Objects.equal(checkDefinition.getOwningTeam(), other.getOwningTeam())
                && Objects.equal(checkDefinition.getEntities(), other.getEntities())
                && Objects.equal(checkDefinition.getInterval(), other.getInterval())
                && Objects.equal(checkDefinition.getCommand(), other.getCommand())
                && Objects.equal(checkDefinition.getStatus(), other.getStatus())
                && Objects.equal(checkDefinition.getSourceUrl(), other.getSourceUrl())
                && Objects.equal(checkDefinition.getLastModifiedBy(), other.getLastModifiedBy());

    }

    public void describeTo(final Description desc) {
        desc.appendText("{Id is ").appendValue(checkDefinition.getId()).appendText(", name is ")
            .appendValue(checkDefinition.getName()).appendText(", description is ")
            .appendValue(checkDefinition.getDescription()).appendText(", technical details are ")
            .appendValue(checkDefinition.getTechnicalDetails()).appendText(", potential analysis is ")
            .appendValue(checkDefinition.getPotentialAnalysis()).appendText(", potential impact is ")
            .appendValue(checkDefinition.getPotentialImpact()).appendText(", potential solution is ")
            .appendValue(checkDefinition.getPotentialSolution()).appendText(", owning team is ")
            .appendValue(checkDefinition.getOwningTeam()).appendText(", entities are ")
            .appendValue(checkDefinition.getEntities()).appendText(", interval is ")
            .appendValue(checkDefinition.getInterval()).appendText(", command is ")
            .appendValue(checkDefinition.getCommand()).appendText(", source url is ")
            .appendValue(checkDefinition.getStatus()).appendText(", status is ")
            .appendValue(checkDefinition.getSourceUrl()).appendText(", last modified by ")
            .appendValue(checkDefinition.getLastModifiedBy()).appendText("}");
    }

    // factory methods for fluent language
    public static Matcher<? super CheckDefinition> equalTo(final CheckDefinition checkDefinition) {
        Preconditions.checkNotNull(checkDefinition, "checkDefinition");
        return new CheckDefinitionIsEqual(checkDefinition);
    }

    public static Collection<Matcher<? super CheckDefinition>> equalTo(
            final Iterable<CheckDefinition> checkDefinitions) {
        Preconditions.checkNotNull(checkDefinitions, "checkDefinitions");

        final List<Matcher<? super CheckDefinition>> matchers = new LinkedList<>();
        for (final CheckDefinition checkDefinition : checkDefinitions) {
            matchers.add(new CheckDefinitionIsEqual(checkDefinition));
        }

        return matchers;
    }
}
