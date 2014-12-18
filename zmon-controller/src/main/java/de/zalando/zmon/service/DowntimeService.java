package de.zalando.zmon.service;

import java.util.List;
import java.util.Set;

import de.zalando.zmon.domain.DowntimeDetails;
import de.zalando.zmon.domain.DowntimeRequest;
import de.zalando.zmon.rest.DowntimeGroup;

public interface DowntimeService {

    List<String> scheduleDowntime(DowntimeRequest request);

    DowntimeGroup scheduleDowntimeGroup(DowntimeGroup group);

    List<DowntimeDetails> getDowntimes(Set<Integer> alertDefinitionIds);

    DowntimeGroup deleteDowntimeGroup(String groupId);

    void deleteDowntimes(Set<String> downtimeId);
}
