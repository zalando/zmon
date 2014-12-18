package de.zalando.zmon.security;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.lang3.StringEscapeUtils;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;

/**
 * This implementation sends a 403 (SC_FORBIDDEN) HTTP error code and JSON message. Created by pribeiro on 20/08/14.
 */
public class JSONAccessDeniedHandler implements AccessDeniedHandler {

    @Override
    public void handle(final HttpServletRequest request, final HttpServletResponse response,
            final AccessDeniedException accessDeniedException) throws IOException, ServletException {
        if (!response.isCommitted()) {

            // TODO think in a better way to set the content type
            response.setContentType("application/json;charset=UTF-8");
            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
            response.getWriter().write("{\"message\":\""
                    + StringEscapeUtils.escapeJson(accessDeniedException.getMessage()) + "\"}");
        }
    }
}
