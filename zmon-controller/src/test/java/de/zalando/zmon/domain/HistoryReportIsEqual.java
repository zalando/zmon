package de.zalando.zmon.domain;

import java.util.Collection;
import java.util.LinkedList;
import java.util.List;

import org.hamcrest.BaseMatcher;
import org.hamcrest.Description;
import org.hamcrest.Matcher;

import com.google.common.base.Objects;
import com.google.common.base.Preconditions;

public class HistoryReportIsEqual extends BaseMatcher<HistoryReport> {

    private final HistoryReport historyReport;

    public HistoryReportIsEqual(final HistoryReport historyReport) {
        this.historyReport = historyReport;
    }

    public boolean matches(final Object o) {
        final HistoryReport other = (HistoryReport) o;

        return Objects.equal(historyReport.getTime(), other.getTime())
                && Objects.equal(historyReport.getTypeId(), other.getTypeId())
                && Objects.equal(historyReport.getTypeName(), other.getTypeName())
                && Objects.equal(historyReport.getAttributes(), other.getAttributes())
                && Objects.equal(historyReport.getAction(), other.getAction())
                && Objects.equal(historyReport.getChangedAttributes(), other.getChangedAttributes())
                && Objects.equal(historyReport.getHistoryType(), other.getHistoryType());
    }

    public void describeTo(final Description desc) {
        desc.appendText("{Time is ").appendValue(historyReport.getTime()).appendText(", type id is ")
            .appendValue(historyReport.getTypeId()).appendText(", type name is ")
            .appendValue(historyReport.getTypeName()).appendText(", attributes are ")
            .appendValue(historyReport.getAttributes()).appendText(", action is ")
            .appendValue(historyReport.getAction()).appendText(", changed attributes are ")
            .appendValue(historyReport.getChangedAttributes()).appendText(", history type is ")
            .appendValue(historyReport.getHistoryType()).appendText("}");
    }

    // factory methods for fluent language
    public static Matcher<? super HistoryReport> equalTo(final HistoryReport historyReport) {
        Preconditions.checkNotNull(historyReport, "historyReport");

        return new HistoryReportIsEqual(historyReport);
    }

    public static Collection<Matcher<? super HistoryReport>> equalTo(final Iterable<HistoryReport> historyReports) {
        Preconditions.checkNotNull(historyReports, "historyReport");

        final List<Matcher<? super HistoryReport>> matchers = new LinkedList<>();
        for (final HistoryReport historyReport : historyReports) {
            matchers.add(new HistoryReportIsEqual(historyReport));
        }

        return matchers;
    }
}
