package de.zalando.zmon.validation;

import java.util.Map;
import java.util.regex.Pattern;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

import de.zalando.zmon.annotation.ParameterKey;
import de.zalando.zmon.domain.Parameter;

/**
 * Created by pribeiro on 27/06/14.
 */
public class AlertParameterValidator implements ConstraintValidator<ParameterKey, Map<String, Parameter>> {

    private static final Pattern KEY_FORMAT = Pattern.compile("^[_a-zA-Z][_a-zA-Z0-9]*");

    @Override
    public void initialize(final ParameterKey constraintAnnotation) { }

    @Override
    public boolean isValid(final Map<String, Parameter> value, final ConstraintValidatorContext context) {

        if (value != null) {
            for (final String key : value.keySet()) {
                if (key == null || !KEY_FORMAT.matcher(key).matches()) {
                    return false;
                }
            }
        }

        return true;
    }
}
