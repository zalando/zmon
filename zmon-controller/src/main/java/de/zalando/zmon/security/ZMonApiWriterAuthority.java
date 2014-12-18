package de.zalando.zmon.security;

import java.util.Set;

import org.springframework.security.core.GrantedAuthority;

import com.google.common.collect.ImmutableSet;

/**
 */
public class ZMonApiWriterAuthority extends ZMonViewerAuthority {

    private static final long serialVersionUID = 1L;

    public static final GrantedAuthorityFactory FACTORY = new GrantedAuthorityFactory() {
        @Override
        public GrantedAuthority create(final String username, final Set<String> projects) {
            return new ZMonApiWriterAuthority(username, ImmutableSet.copyOf(projects));
        }
    };

    public ZMonApiWriterAuthority(final String userName, final ImmutableSet<String> teams) {
        super(userName, teams);
    }

    @Override
    protected ZMonRole getZMonRole() {
        return ZMonRole.API_WRITER;
    }
}
