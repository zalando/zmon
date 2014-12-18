package de.zalando.zmon.domain;

import java.util.ArrayList;
import java.util.List;

import com.fasterxml.jackson.databind.JsonNode;

public class CheckHistoryGroupResult {

    public String key;
    public final List<List<JsonNode>> values = new ArrayList<>();
}
