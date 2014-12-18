package de.zalando.zmon.exception;

import java.util.Collection;

import org.springframework.security.core.GrantedAuthority;

public class ZMonAuthorizationException extends ZMonRuntimeException {

    private static final long serialVersionUID = 1L;

    private final String userName;
    private final Collection<? extends GrantedAuthority> authorities;
    private final Object details;

    public ZMonAuthorizationException(final String userName, final Collection<? extends GrantedAuthority> authorities,
            final String msg) {
        this(userName, authorities, msg, null);
    }

    public ZMonAuthorizationException(final String userName, final Collection<? extends GrantedAuthority> authorities,
            final String msg, final Object details) {
        super(msg);
        this.userName = userName;
        this.authorities = authorities;
        this.details = details;
    }

    public String getUserName() {
        return userName;
    }

    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    public Object getDetails() {
        return details;
    }
}
