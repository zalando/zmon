CREATE OR REPLACE FUNCTION get_alert_ids_by_status (
    IN status zzm_data.definition_status
) RETURNS SETOF int AS
$BODY$
    SELECT adt_id
      FROM zzm_data.alert_definition_tree
     WHERE adt_status = status
       AND adt_template = 'f';
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;