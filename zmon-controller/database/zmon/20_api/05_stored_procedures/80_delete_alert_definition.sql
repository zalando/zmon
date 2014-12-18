CREATE OR REPLACE FUNCTION delete_alert_definition (
     IN p_alert_definition_id  int,
    OUT status                 operation_status,
    OUT error_message          text,
    OUT entity                 alert_definition_type
) AS
$BODY$
DECLARE
    l_children int[];
BEGIN

         SELECT array_agg(adt_id)
           INTO l_children
           FROM zzm_data.alert_definition_tree
          WHERE adt_parent_id = p_alert_definition_id;

             IF ARRAY_LENGTH(l_children, 1) IS NOT NULL AND ARRAY_LENGTH(l_children, 1) > 0 THEN
                status := 'DELETE_NON_LEAF_ALERT_DEFINITION';
                error_message := 'Could not delete an alert definition with descendants: ' || l_children::text;
                RETURN;
            END IF;

    -- delete all comments
    DELETE FROM zzm_data.alert_comment
          WHERE ac_alert_definition_id = p_alert_definition_id;

    -- delete alert definition
    DELETE FROM zzm_data.alert_definition_tree
          WHERE adt_id = p_alert_definition_id
      RETURNING adt_id,
                adt_name,
                adt_description,
                adt_team,
                adt_responsible_team,
                adt_entities,
                adt_condition,
                adt_notifications,
                adt_check_definition_id,
                adt_status,
                adt_priority,
                adt_last_modified,
                adt_last_modified_by,
                adt_period,
                adt_template,
                adt_parent_id,
                adt_parameters
           INTO entity.id,
                entity.name,
                entity.description,
                entity.team,
                entity.responsible_team,
                entity.entities,
                entity.condition,
                entity.notifications,
                entity.check_definition_id,
                entity.status,
                entity.priority,
                entity.last_modified,
                entity.last_modified_by,
                entity.period,
                entity.template,
                entity.parent_id,
                entity.parameters;

    status := 'SUCCESS';
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
