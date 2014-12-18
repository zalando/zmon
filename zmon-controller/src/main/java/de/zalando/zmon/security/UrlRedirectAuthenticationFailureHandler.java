package de.zalando.zmon.security;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.AuthenticationFailureHandler;

import org.springframework.util.StringUtils;

import com.google.common.base.Preconditions;

public class UrlRedirectAuthenticationFailureHandler implements AuthenticationFailureHandler {

    private final String resourcePath;
    private final String targetUrlParameter;

    public UrlRedirectAuthenticationFailureHandler(final String resourcePath, final String targetUrlParameter) {
        this.resourcePath = Preconditions.checkNotNull(resourcePath, "resourcePath");
        this.targetUrlParameter = Preconditions.checkNotNull(targetUrlParameter, "targetUrlParameter");
    }

    @Override
    public void onAuthenticationFailure(final HttpServletRequest request, final HttpServletResponse response,
            final AuthenticationException exception) throws IOException, ServletException {

        final String nextPage = request.getParameter(targetUrlParameter);
        if (StringUtils.hasText(nextPage)) {
            request.setAttribute(targetUrlParameter, nextPage);
        }

        request.setAttribute("error", "login_error");
        request.getRequestDispatcher(resourcePath).forward(request, response);
    }
}
