package de.zalando.zmon.validation;

import java.util.List;
import java.util.Map;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

import de.zalando.zmon.annotation.ContainsEntityKey;

public class ContainsEntityKeyValidator implements ConstraintValidator<ContainsEntityKey, List<Map<String, String>>> {

    private ContainsEntityKey entitiesFilter;

    @Override
    public void initialize(final ContainsEntityKey constraintAnnotation) {
        this.entitiesFilter = constraintAnnotation;
    }

    @Override
    public boolean isValid(final List<Map<String, String>> value, final ConstraintValidatorContext context) {
        if (value == null || value.isEmpty()) {
            return false;
        }

        for (final Map<String, String> entity : value) {
            if (entity == null) {
                return false;
            }

            for (final String key : entitiesFilter.keys()) {
                if (!entity.containsKey(key)) {
                    return false;
                }
            }
        }

        return true;
    }
}
