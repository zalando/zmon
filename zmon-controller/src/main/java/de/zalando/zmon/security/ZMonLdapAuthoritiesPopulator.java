package de.zalando.zmon.security;

import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.naming.NamingEnumeration;
import javax.naming.NamingException;
import javax.naming.directory.Attribute;

import org.springframework.ldap.core.DirContextOperations;
import org.springframework.ldap.support.LdapUtils;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.ldap.userdetails.LdapAuthoritiesPopulator;

import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

public class ZMonLdapAuthoritiesPopulator implements LdapAuthoritiesPopulator {

    private static final String TEAM_CAPTURE_TOKEN = "team";

    private final String groupAttribute;
    private final Pattern teamPattern;
    private final ImmutableMap<String, GrantedAuthorityFactory> availableRoles;

    public ZMonLdapAuthoritiesPopulator(final String groupAttribute, final String adminGroup, final String leadGroup,
            final String userGroup, final String viewerGroup, final String apiReaderGroup, final String apiWriterGroup,
            final String teamRegex) {
        this.groupAttribute = Preconditions.checkNotNull(groupAttribute, "groupAttribute");
        this.teamPattern = Pattern.compile(Preconditions.checkNotNull(teamRegex, "teamRegex"),
                Pattern.CASE_INSENSITIVE);
        availableRoles = ImmutableMap.<String, GrantedAuthorityFactory>builder()
                                     .put(Preconditions.checkNotNull(adminGroup, "adminGroup"),
                                         ZMonAdminAuthority.FACTORY)
                                     .put(Preconditions.checkNotNull(leadGroup, "leadGroup"), ZMonLeadAuthority.FACTORY)
                                     .put(Preconditions.checkNotNull(userGroup, "userGroup"), ZMonUserAuthority.FACTORY)
                                     .put(Preconditions.checkNotNull(viewerGroup, "viewerGroup"),
                                         ZMonViewerAuthority.FACTORY)
                                     .put(Preconditions.checkNotNull(apiReaderGroup, "apiReaderGroup"),
                                         ZMonApiReaderAuthority.FACTORY)
                                     .put(Preconditions.checkNotNull(apiWriterGroup, "apiWriterGroup"),
                ZMonApiWriterAuthority.FACTORY).build();
    }

    @Override
    public Collection<? extends GrantedAuthority> getGrantedAuthorities(final DirContextOperations userData,
            final String username) {

        Collection<? extends GrantedAuthority> grantedAuthorities = Collections.emptyList();
        try {
            final Attribute attribute = userData.getAttributes().get(groupAttribute);
                grantedAuthorities = getAuthoritiesFromLdapGroups(attribute, username);
        } catch (final NamingException e) {
            throw LdapUtils.convertLdapException(e);
        }

        return grantedAuthorities;
    }

    private List<GrantedAuthority> getAuthoritiesFromLdapGroups(final Attribute attribute, final String username)
        throws NamingException {

        final Map<String, GrantedAuthorityFactory> roles = new HashMap<>();
        final ImmutableSet.Builder<String> projectsBuilder = ImmutableSet.builder();

        if (attribute != null) {
        final NamingEnumeration<?> e = attribute.getAll();
        while (e.hasMore()) {
            final String groupDN = e.next().toString();
            final GrantedAuthorityFactory grantedAuthorityFactory = availableRoles.get(groupDN);
            if (grantedAuthorityFactory != null) {
                roles.put(groupDN, grantedAuthorityFactory);
            } else {

                // check if it's a group
                final Matcher projectGroupMatcher = teamPattern.matcher(groupDN);
                if (projectGroupMatcher.matches()) {
                    final String project = projectGroupMatcher.group(TEAM_CAPTURE_TOKEN);
                    if (project != null) {
                        projectsBuilder.add(project);
                    }
                }
            }
        }
        }
        
        final GrantedAuthorityFactory wildcardGrantedAuthorityFactory = availableRoles.get("*");
         
        if (wildcardGrantedAuthorityFactory != null) {
            roles.put("*", wildcardGrantedAuthorityFactory);
        }

        final ImmutableSet<String> projects = projectsBuilder.build();
        final List<GrantedAuthority> authorities = new LinkedList<>();
        for (final GrantedAuthorityFactory factory : roles.values()) {
            authorities.add(factory.create(username, projects));
        }

        return authorities;
    }
}
