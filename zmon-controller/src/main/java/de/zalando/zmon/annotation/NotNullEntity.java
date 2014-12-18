package de.zalando.zmon.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;

import de.zalando.zmon.validation.NotNullEntityValidator;

@Target({ ElementType.METHOD, ElementType.FIELD })
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = NotNullEntityValidator.class)
public @interface NotNullEntity {

    String message() default "{entities.filter.null}";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
