CREATE OR REPLACE FUNCTION add_alert_comment (
     IN comment           alert_comment,
     OUT status           operation_status,
     OUT error_message    text,
     OUT entity           alert_comment
) AS
$BODY$
BEGIN
    INSERT INTO zzm_data.alert_comment (
        ac_created_by,
        ac_last_modified_by,
        ac_comment,
        ac_alert_definition_id,
        ac_entity_id
        )
      VALUES (
         comment.created_by,
         comment.last_modified_by,
         comment.comment,
         comment.alert_definition_id,
         comment.entity_id
      ) RETURNING ac_id,
                  ac_created,
                  ac_created_by,
                  ac_last_modified,
                  ac_last_modified_by,
                  ac_comment,
                  ac_alert_definition_id,
                  ac_entity_id I
             INTO entity.id,
                  entity.created,
                  entity.created_by,
                  entity.last_modified,
                  entity.last_modified_by,
                  entity.comment,
                  entity.alert_definition_id,
                  entity.entity_id;

    status := 'SUCCESS';

 -- handle foreign key violation and return an error code
EXCEPTION WHEN foreign_key_violation THEN
    status := 'ALERT_DEFINITION_NOT_FOUND';
    error_message := 'Alert definition with id ' || comment.alert_definition_id || ' not found';
END;
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
