package de.zalando.zmon.listener;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.context.ApplicationListener;

import org.springframework.security.authentication.event.AbstractAuthenticationEvent;
import org.springframework.security.authentication.event.AbstractAuthenticationFailureEvent;
import org.springframework.security.authentication.event.AuthenticationSuccessEvent;

import org.springframework.stereotype.Component;

@Component
public class AuthenticationEventListener implements ApplicationListener<AbstractAuthenticationEvent> {

    private static final Logger LOG = LoggerFactory.getLogger(AuthenticationEventListener.class);

    @Override
    public void onApplicationEvent(final AbstractAuthenticationEvent event) {
        if (event instanceof AuthenticationSuccessEvent) {

            // log success event as info
            LOG.info("User [{}] successfully authenticated", event.getAuthentication().getName());
        } else if (event instanceof AbstractAuthenticationFailureEvent) {

            LOG.warn("User [{}] authentication failed: [{}]", event.getAuthentication().getName(),
                ((AbstractAuthenticationFailureEvent) event).getException().getMessage());
        }
    }
}
