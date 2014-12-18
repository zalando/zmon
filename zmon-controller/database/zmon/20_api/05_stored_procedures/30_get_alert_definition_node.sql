CREATE OR REPLACE FUNCTION get_alert_definition_node (
     IN alert_definition_id int
) RETURNS alert_definition_type AS
$BODY$
    SELECT adt_id,
           adt_name,
           adt_description,
           adt_team,
           adt_responsible_team,
           adt_entities,
           adt_entities_exclude,
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
           adt_parameters,
           adt_tags
      FROM zzm_data.alert_definition_tree
     WHERE adt_id = alert_definition_id;
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;
