CREATE OR REPLACE FUNCTION get_alert_ids_by_check_id (
    IN p_check_definition_id int
) RETURNS SETOF int AS
$BODY$
    WITH RECURSIVE alert_definition(ad_id, ad_parent_id, ad_check_definition_id, ad_template) AS (
            SELECT adt_id,
                   adt_parent_id,
                   adt_check_definition_id,
                   adt_template
              FROM zzm_data.alert_definition_tree
             WHERE adt_check_definition_id = p_check_definition_id
             UNION
            SELECT adt_id,
                   adt_parent_id,
                   COALESCE(adt_check_definition_id, ad_check_definition_id),
                   adt_template
              FROM zzm_data.alert_definition_tree
              JOIN alert_definition ON adt_parent_id = ad_id
             WHERE COALESCE(adt_check_definition_id, ad_check_definition_id) = p_check_definition_id
    )
    SELECT ad_id
      FROM alert_definition
     WHERE NOT ad_template;
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;
