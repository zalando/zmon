package de.zalando.zmon.validation;

import java.util.List;
import java.util.Map;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

import de.zalando.zmon.annotation.NotNullEntity;

public class NotNullEntityValidator implements ConstraintValidator<NotNullEntity, List<Map<String, String>>> {

    @Override
    public void initialize(final NotNullEntity constraintAnnotation) { }

    @Override
    public boolean isValid(final List<Map<String, String>> value, final ConstraintValidatorContext context) {
        if (value != null && !value.isEmpty()) {
            for (final Map<String, String> entity : value) {
                if (entity == null || entity.containsKey(null) || entity.containsValue(null)) {
                    return false;
                }
            }
        }

        return true;
    }
}
