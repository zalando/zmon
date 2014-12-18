CREATE OR REPLACE FUNCTION delete_alert_comment (
     IN comment_id    int
) RETURNS alert_comment AS
$BODY$
DECLARE
    l_comment alert_comment;
BEGIN
    DELETE FROM zzm_data.alert_comment
          WHERE ac_id = comment_id
      RETURNING ac_id,
                ac_created,
                ac_created_by,
                ac_last_modified,
                ac_last_modified_by,
                ac_comment,
                ac_alert_definition_id,
                ac_entity_id
           INTO l_comment.id,
                l_comment.created,
                l_comment.created_by,
                l_comment.last_modified,
                l_comment.last_modified_by,
                l_comment.comment,
                l_comment.alert_definition_id,
                l_comment.entity_id;

    RETURN l_comment;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
