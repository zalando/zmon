package de.zalando.zmon.validation;

import java.util.Calendar;
import java.util.TimeZone;

import org.springframework.stereotype.Component;

import org.springframework.validation.Errors;
import org.springframework.validation.Validator;

import de.zalando.zmon.domain.AbstractDowntime;

@Component
public class DowntimeValidator implements Validator {

    @Override
    public boolean supports(final Class<?> clazz) {
        return AbstractDowntime.class.isAssignableFrom(clazz);
    }

    @Override
    public void validate(final Object target, final Errors errors) {
        final AbstractDowntime downtimeRequest = (AbstractDowntime) target;

        if (downtimeRequest.getStartTime() >= downtimeRequest.getEndTime()) {
            errors.rejectValue("startTime", "DowntimeValidator.startTime.overlap", "Start date must precede end date");
        }

        final Calendar now = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        if (downtimeRequest.getEndTime() <= now.getTimeInMillis() / 1000) {
            errors.rejectValue("endTime", "DowntimeValidator.endTime.expired", "End time expired");
        }

        now.add(Calendar.YEAR, 1);
        if (downtimeRequest.getEndTime() > now.getTimeInMillis() / 1000) {
            errors.rejectValue("endTime", "DowntimeValidator.endTime.limitExceeded",
                "End time limit exceeded (maximum is 1 year)");
        }
    }

}
