package de.zalando.zmon.service.impl;

import de.zalando.eventlog.EventLogger;
import de.zalando.zmon.event.ZMonEventType;
import de.zalando.zmon.rest.ZmonGroup;
import de.zalando.zmon.rest.ZmonGroupMember;
import de.zalando.zmon.security.ZMonAuthorityService;
import de.zalando.zmon.service.GroupService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Created by jmussler on 11/11/14.
 */
@Service
public class GroupServiceImpl implements GroupService {

    private final JedisPool redisPool;
    protected final ZMonAuthorityService authorityService;

    private static final EventLogger EVENT_LOG = EventLogger.getLogger(AlertServiceImpl.class);

    public void createGroupIfNotExists(Jedis jedis, String groupId) {
        jedis.hsetnx("zmon:groups", groupId, groupId);
    }

    @Override
    public long addMember(String groupId, String memberId) {
        Jedis jedis = redisPool.getResource();
        try {
            createGroupIfNotExists(jedis, groupId);
            return jedis.sadd(getMembersKey(groupId),memberId);
        }
        finally {
            redisPool.returnResource(jedis);
        }
    }

    @Override
    public long removeMember(String groupId, String memberId) {
        Jedis jedis = redisPool.getResource();
        try {
            return jedis.srem(getMembersKey(groupId),memberId);
        }
        finally {
            redisPool.returnResource(jedis);
        }
    }

    @Override
    public long clearActive(String groupId) {
        Jedis jedis = redisPool.getResource();
        try {
            EVENT_LOG.log(ZMonEventType.GROUP_MODIFIED, authorityService.getUserName(), "clear-active", groupId);
            jedis.del(getActiveKey(groupId));
            return 0;
        }
        finally {
            redisPool.returnResource(jedis);
        }
    }

    @Override
    public long addToActive(String groupId, String memberId) {
        Jedis jedis = redisPool.getResource();
        try {
            ZmonGroup g = getGroup(groupId);

            if(g.members.contains(memberId)) {
                EVENT_LOG.log(ZMonEventType.GROUP_MODIFIED, authorityService.getUserName(), "activate", groupId, memberId);
                return jedis.sadd(getActiveKey(groupId), memberId);
            }
            return -1;
        }
        finally {
            redisPool.returnResource(jedis);
        }
    }

    @Override
    public long removeFromActive(String groupId, String memberId) {
        Jedis jedis = redisPool.getResource();
        try {
            EVENT_LOG.log(ZMonEventType.GROUP_MODIFIED, authorityService.getUserName(), "remove-active", groupId, memberId);
            return jedis.srem(getActiveKey(groupId), memberId);
        }
        finally {
            redisPool.returnResource(jedis);
        }

    }

    @Override
    public long addPhone(String memberId, String phone) {
        Jedis jedis = redisPool.getResource();
        try {
            EVENT_LOG.log(ZMonEventType.GROUP_MODIFIED, authorityService.getUserName(), "add-phone", null, memberId, phone);
            return jedis.sadd(getMemberPhoneKey(memberId),phone);
        }
        finally {
            redisPool.returnResource(jedis);
        }
    }

    protected String getMemberPhoneKey(String memberId) {
        return "zmon:member:"+memberId+":phone";
    }

    @Override
    public long removePhone(String memberId, String phone) {
        Jedis jedis = redisPool.getResource();
        try {
            EVENT_LOG.log(ZMonEventType.GROUP_MODIFIED, authorityService.getUserName(), "remove-phone", null, memberId, phone);
            return jedis.srem(getMemberPhoneKey(memberId),phone);
        }
        finally {
            redisPool.returnResource(jedis);
        }
    }

    public void setName(String memberId, String name) {
        Jedis jedis = redisPool.getResource();
        try {
            jedis.set("zmon:member:"+memberId+":name",name);
        }
        finally {
            redisPool.returnResource(jedis);
        }
    }

    @Override
    public ZmonGroupMember getMember(String memberId) {
        ZmonGroupMember m = new ZmonGroupMember();
        Jedis jedis = redisPool.getResource();
        try {
            Set<String> phones = jedis.smembers(getMemberPhoneKey(memberId));
            String name = jedis.get("zmon:member:"+memberId+":name");
            if(name==null) {
                name = "";
            }
            m.name = name;
            m.phones.addAll(phones);
            m.id = memberId;
            m.email = memberId;
        }
        finally {
            redisPool.returnResource(jedis);
        }
        return m;
    }

    @Autowired
    public GroupServiceImpl(JedisPool pool, ZMonAuthorityService authorityService) {
        this.redisPool = pool;
        this.authorityService = authorityService;
    }

    protected String getMembersKey(String id) {
        return "zmon:group:"+id+":members";
    }

    protected String getActiveKey(String id) {
        return "zmon:group:"+id+":active";
    }

    public ZmonGroup getGroup(String id) {

        Jedis jedis = redisPool.getResource();
        try {
            Set<String> members = jedis.smembers(getMembersKey(id));
            Set<String> active = jedis.smembers(getActiveKey(id));

            ZmonGroup g = new ZmonGroup();
            g.id = id;
            g.name = id;

            g.members.addAll(members);
            g.active.addAll(active);

            return g;
        }
        finally {
            redisPool.returnResource(jedis);
        }

    }

    @Override
    public List<ZmonGroup> getAllGroups() {
        List<ZmonGroup> groups = new ArrayList<>();

        Jedis jedis = redisPool.getResource();
        try {
            Map<String, String> gs = jedis.hgetAll("zmon:groups");
            for(String id : gs.keySet()) {
                Set<String> members = jedis.smembers(getMembersKey(id));
                Set<String> active = jedis.smembers(getActiveKey(id));

                ZmonGroup g = new ZmonGroup();
                g.id = id;
                g.name = gs.get(id);

                g.members.addAll(members);
                g.active.addAll(active);

                groups.add(g);
            }
        }
        finally {
            redisPool.returnResource(jedis);
        }

        return groups;
    }
}
