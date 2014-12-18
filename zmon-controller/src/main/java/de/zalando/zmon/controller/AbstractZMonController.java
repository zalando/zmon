package de.zalando.zmon.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.beans.TypeMismatchException;

import org.springframework.http.HttpStatus;
import org.springframework.http.converter.HttpMessageNotReadableException;

import org.springframework.ui.ModelMap;

import org.springframework.util.ClassUtils;

import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;

import de.zalando.zmon.exception.ZMonAuthorizationException;
import de.zalando.zmon.exception.ZMonException;

/**
 * Abstract zmon controller that should contain common code used across all controllers like exception handlers.
 *
 * @author  pribeiro
 */
public abstract class AbstractZMonController {

    private static final Logger LOG = LoggerFactory.getLogger(AbstractZMonController.class);

    public static final String ERROR_MESSAGE_KEY = "message";

    // handle malformed messages
    @ExceptionHandler(MissingServletRequestParameterException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ResponseBody
    public ModelMap handleMissingServletRequestParameterException(final MissingServletRequestParameterException e) {
        LOG.warn("Malformed request [{}]: [{}]", e.getClass().getSimpleName(), e.getMessage());

        return
            new ModelMap().addAttribute(ERROR_MESSAGE_KEY, new StringBuilder("Parameter '").append(
                    e.getParameterName()).append("' with type '").append(e.getParameterType()).append("' is missing"));
    }

    // handle wrong types
    @ExceptionHandler(TypeMismatchException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ResponseBody
    public ModelMap handleTypeMismatchException(final TypeMismatchException e) {
        LOG.warn("Malformed request [{}]: [{}]", e.getClass().getSimpleName(), e.getMessage());

        return
            new ModelMap().addAttribute(ERROR_MESSAGE_KEY, new StringBuilder("Failed to convert value of type '")
                    .append(e.getValue() == null ? null : ClassUtils.getShortName(e.getValue().getClass())).append(
                    "'").append(
                    e.getRequiredType() != null
                        ? " to required type '" + ClassUtils.getShortName(e.getRequiredType()) + "'" : "").append(
                    " for input value: ").append(e.getValue()));
    }

    // handle malformed messages
    @ExceptionHandler(HttpMessageNotReadableException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ResponseBody
    public ModelMap handleHttpMessageNotReadableException(final HttpMessageNotReadableException e) {
        LOG.warn("Malformed request [{}]: [{}]", e.getClass().getSimpleName(), e.getMessage());

        // return default message
        return new ModelMap().addAttribute(ERROR_MESSAGE_KEY, "Could not read request");
    }

    // handle malformed requests
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ResponseBody
    public ModelMap handleMethodArgumentNotValidException(final MethodArgumentNotValidException e) {
        LOG.warn("Malformed request [{}]: [{}]", e.getClass().getSimpleName(), e.getMessage());

        // return default message
        return new ModelMap().addAttribute(ERROR_MESSAGE_KEY, e.getBindingResult().getFieldError().getDefaultMessage());
    }

    // handle security errors
    @ExceptionHandler(ZMonAuthorizationException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    @ResponseBody
    public ModelMap handleZMonAuthorizationException(final ZMonAuthorizationException e) {
        LOG.warn("Unauthorized user action [{}] with authorities [{}]: [{}]", e.getUserName(), e.getAuthorities(),
            e.getDetails());

        return new ModelMap().addAttribute(ERROR_MESSAGE_KEY, e.getMessage());
    }

    // handle business errors
    @ExceptionHandler(ZMonException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ResponseBody
    public ModelMap handleZMonException(final Exception e) {
        LOG.warn("Functional problem [{}] occurred: [{}]", e.getClass().getSimpleName(), e.getMessage());

        return new ModelMap().addAttribute(ERROR_MESSAGE_KEY, e.getMessage());
    }

    // handle all other exceptions
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    @ResponseBody
    public void handleRuntimeException(final Exception e) {
        LOG.error("Technical problem occurred", e);
    }
}
