package de.zalando.zmon.security;

import java.util.Set;

import org.springframework.security.core.GrantedAuthority;

import com.google.common.collect.ImmutableSet;

/**
 */
public class ZMonApiReaderAuthority extends ZMonViewerAuthority {

    private static final long serialVersionUID = 1L;

    public static final GrantedAuthorityFactory FACTORY = new GrantedAuthorityFactory() {
        @Override
        public GrantedAuthority create(final String username, final Set<String> projects) {
            return new ZMonApiReaderAuthority(username, ImmutableSet.copyOf(projects));
        }
    };

    public ZMonApiReaderAuthority(final String userName, final ImmutableSet<String> teams) {
        super(userName, teams);
    }

    @Override
    protected ZMonRole getZMonRole() {
        return ZMonRole.API_READER;
    }
}
