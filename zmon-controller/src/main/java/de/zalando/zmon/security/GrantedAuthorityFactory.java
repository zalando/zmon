package de.zalando.zmon.security;

import java.util.Set;

import org.springframework.security.core.GrantedAuthority;

/**
 * Created by pribeiro on 19/08/14.
 */
public interface GrantedAuthorityFactory {

    GrantedAuthority create(String username, Set<String> projects);
}
