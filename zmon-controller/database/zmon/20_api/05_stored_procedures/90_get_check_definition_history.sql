CREATE OR REPLACE FUNCTION get_check_definition_history (
     IN p_check_definition_id int,
     IN p_limit               int,
     IN p_from                timestamptz,
     IN p_to                  timestamptz
) RETURNS SETOF history_entry AS
$BODY$
    SELECT cdh_id,
           cdh_timestamp,
           cdh_action,
           cdh_row_data,
           cdh_changed_fields,
           cdh_user_name,
           cdh_check_definition_id,
           'CHECK_DEFINITION'::history_type
      FROM zzm_data.check_definition_history
     WHERE cdh_check_definition_id = p_check_definition_id
       AND (p_from IS NULL OR cdh_timestamp >= p_from)
       AND (p_to IS NULL OR cdh_timestamp <= p_to)
  ORDER BY cdh_timestamp DESC, cdh_id DESC
     LIMIT p_limit;
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;
