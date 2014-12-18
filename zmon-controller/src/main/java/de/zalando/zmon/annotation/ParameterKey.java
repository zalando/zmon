package de.zalando.zmon.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;

import de.zalando.zmon.validation.AlertParameterValidator;

@Target({ ElementType.METHOD, ElementType.FIELD })
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = AlertParameterValidator.class)
public @interface ParameterKey {

    String message() default "{alert.condition.malformed.key}";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
