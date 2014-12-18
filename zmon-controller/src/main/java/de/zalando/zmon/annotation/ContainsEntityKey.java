package de.zalando.zmon.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import javax.validation.Constraint;
import javax.validation.Payload;

import de.zalando.zmon.validation.ContainsEntityKeyValidator;

@Target({ ElementType.METHOD, ElementType.FIELD })
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = ContainsEntityKeyValidator.class)
public @interface ContainsEntityKey {

    String message() default "{entities.filter.type.missing}";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};

    String[] keys();
}
