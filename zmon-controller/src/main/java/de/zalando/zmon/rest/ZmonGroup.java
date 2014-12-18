package de.zalando.zmon.rest;

import java.util.HashSet;
import java.util.Set;

/**
 * Created by jmussler on 11/11/14.
 */
public class ZmonGroup {
    public String name;
    public String id;

    public final Set<String> members;
    public final Set<String> active;

    public ZmonGroup() {
        members = new HashSet<>();
        active = new HashSet<>();
    }
}
