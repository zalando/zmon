package de.zalando.zmon.generator;

import java.util.Date;

import de.zalando.zmon.domain.AlertComment;

public class AlertCommentGenerator implements DataGenerator<AlertComment> {

    @Override
    public AlertComment generate() {
        final Date now = new Date();
        final AlertComment comment = new AlertComment();
        comment.setCreated(now);
        comment.setCreatedBy("pribeiro");
        comment.setLastModified(now);
        comment.setLastModifiedBy("pribeiro");
        comment.setComment("comment");
        comment.setEntityId("myhost123");

        return comment;
    }
}
