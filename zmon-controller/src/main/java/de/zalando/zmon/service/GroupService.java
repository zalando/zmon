package de.zalando.zmon.service;

import de.zalando.zmon.rest.ZmonGroup;
import de.zalando.zmon.rest.ZmonGroupMember;

import java.util.List;

/**
 * Created by jmussler on 11/11/14.
 */
public interface GroupService {
    public List<ZmonGroup> getAllGroups();
    public long addMember(String groupId, String memberId);
    public long removeMember(String groupId, String memberId);
    public long clearActive(String groupId);
    public long addToActive(String groupId, String memberId);
    public long removeFromActive(String groupId, String memberId);

    public long addPhone(String memberId, String phone);
    public long removePhone(String memberId, String phone);
    public ZmonGroupMember getMember(String memberId);
    public void setName(String memberId, String name);
}
