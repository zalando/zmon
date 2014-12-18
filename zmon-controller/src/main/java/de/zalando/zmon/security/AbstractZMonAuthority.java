package de.zalando.zmon.security;

import java.util.Set;

import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableSet;

public abstract class AbstractZMonAuthority implements ZMonAuthority {

    private static final long serialVersionUID = 1L;

    private final String userName;
    private final ImmutableSet<String> teams;

    public AbstractZMonAuthority(final String userName, final ImmutableSet<String> teams) {
        this.userName = Preconditions.checkNotNull(userName, "userName");
        this.teams = Preconditions.checkNotNull(teams, "teams");
    }

    public String getUserName() {
        return userName;
    }

    @Override
    public Set<String> getTeams() {
        return teams;
    }

    @Override
    public String getAuthority() {
        return getZMonRole().getRoleName();
    }

    protected boolean isMemberOfTeam(final String team) {
        if (team != null) {

            // linear time, but we are not expecting a huge set of teams.
            // If we have a huge set of teams, we should use a Patricia trie
            for (final String userTeam : getTeams()) {
                final int length = Math.min(userTeam.length(), team.length());
                if (length >= userTeam.length() && userTeam.regionMatches(true, 0, team, 0, length)) {
                    return true;
                }
            }
        }

        return false;
    }

    protected abstract ZMonRole getZMonRole();

    @Override
    public String toString() {
        final StringBuilder builder = new StringBuilder();
        builder.append(getZMonRole());
        builder.append(" [userName=");
        builder.append(userName);
        builder.append(", teams=");
        builder.append(teams);
        builder.append(']');
        return builder.toString();
    }
}
