CREATE OR REPLACE FUNCTION get_alert_definition_history (
     IN p_alert_definition_id int,
     IN p_limit               int,
     IN p_from                timestamptz,
     IN p_to                  timestamptz
) RETURNS SETOF history_entry AS
$BODY$
      WITH RECURSIVE tree(id, parent_id) AS (
    SELECT adt_id, adt_parent_id
      FROM zzm_data.alert_definition_tree
     WHERE adt_id = p_alert_definition_id
 UNION ALL
    SELECT a.adt_id, a.adt_parent_id
      FROM zzm_data.alert_definition_tree a
      JOIN tree t
        -- prevent circular references
        ON a.adt_id = t.parent_id)

    SELECT adh_id,
           adh_timestamp,
           adh_action,
           adh_row_data,
           adh_changed_fields,
           adh_user_name,
           adh_alert_definition_id,
           'ALERT_DEFINITION'::history_type
      FROM zzm_data.alert_definition_history
      JOIN tree t
        ON adh_alert_definition_id = t.id
     WHERE (p_from IS NULL OR adh_timestamp >= p_from)
       AND (p_to IS NULL OR adh_timestamp <= p_to)
  ORDER BY adh_timestamp DESC, adh_id DESC
     LIMIT p_limit;
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;
