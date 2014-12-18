package de.zalando.zmon.domain;

import java.util.ArrayList;
import java.util.List;

public class CheckHistoryResult {

    public String name;
    public String entityId;
    public final List<CheckHistoryGroupResult> groupResults = new ArrayList<>();
}
