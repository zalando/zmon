package de.zalando.zmon.domain;

import org.hamcrest.BaseMatcher;
import org.hamcrest.Description;
import org.hamcrest.Matcher;

import com.google.common.base.Objects;
import com.google.common.base.Preconditions;

public class CheckDefinitionImportIsEqual extends BaseMatcher<CheckDefinitionImport> {

    private final CheckDefinitionImport toImport;

    public CheckDefinitionImportIsEqual(final CheckDefinitionImport toImport) {
        this.toImport = toImport;
    }

    public boolean matches(final Object o) {
        final CheckDefinitionImport other = (CheckDefinitionImport) o;

        return Objects.equal(toImport.getName(), other.getName())
                && Objects.equal(toImport.getDescription(), other.getDescription())
                && Objects.equal(toImport.getTechnicalDetails(), other.getTechnicalDetails())
                && Objects.equal(toImport.getPotentialAnalysis(), other.getPotentialAnalysis())
                && Objects.equal(toImport.getPotentialImpact(), other.getPotentialImpact())
                && Objects.equal(toImport.getPotentialSolution(), other.getPotentialSolution())
                && Objects.equal(toImport.getOwningTeam(), other.getOwningTeam())
                && Objects.equal(toImport.getEntities(), other.getEntities())
                && Objects.equal(toImport.getInterval(), other.getInterval())
                && Objects.equal(toImport.getCommand(), other.getCommand())
                && Objects.equal(toImport.getStatus(), other.getStatus())
                && Objects.equal(toImport.getSourceUrl(), other.getSourceUrl())
                && Objects.equal(toImport.getLastModifiedBy(), other.getLastModifiedBy());

    }

    public void describeTo(final Description desc) {
        desc.appendText("{name is ").appendValue(toImport.getName()).appendText(", description is ")
            .appendValue(toImport.getDescription()).appendText(", technical details are ")
            .appendValue(toImport.getTechnicalDetails()).appendText(", potential analysis is ")
            .appendValue(toImport.getPotentialAnalysis()).appendText(", potential impact is ")
            .appendValue(toImport.getPotentialImpact()).appendText(", potential solution is ")
            .appendValue(toImport.getPotentialSolution()).appendText(", owning team is ")
            .appendValue(toImport.getOwningTeam()).appendText(", entities are ").appendValue(toImport.getEntities())
            .appendText(", interval is ").appendValue(toImport.getInterval()).appendText(", command is ")
            .appendValue(toImport.getCommand()).appendText(", source url is ").appendValue(toImport.getStatus())
            .appendText(", status is ").appendValue(toImport.getSourceUrl()).appendText(", lastModified by is ")
            .appendValue(toImport.getLastModifiedBy()).appendText("}");
    }

    // factory methods for fluent language
    public static Matcher<? super CheckDefinitionImport> equalTo(final CheckDefinitionImport checkDefinitionImport) {
        Preconditions.checkNotNull(checkDefinitionImport, "checkDefinitionImport");
        return new CheckDefinitionImportIsEqual(checkDefinitionImport);
    }
}
