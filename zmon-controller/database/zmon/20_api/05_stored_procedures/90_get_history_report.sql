CREATE OR REPLACE FUNCTION get_history_report (
     IN p_team               text,
     IN p_responsible_team   text,
     IN p_alert_limit        int,
     IN p_check_limit        int,
     IN p_from               timestamptz,
     IN p_to                 timestamptz
) RETURNS SETOF history_entry AS
$BODY$
    -- get changed alerts
   (SELECT adh_id,
           adh_timestamp,
           adh_action,
           adh_row_data,
           adh_changed_fields,
           adh_user_name,
           adh_alert_definition_id,
           'ALERT_DEFINITION'::history_type
      FROM zzm_data.alert_definition_history
      JOIN zzm_data.alert_definition
        ON adh_alert_definition_id = ad_id
     WHERE ad_status = 'ACTIVE'
       AND ad_team = p_team
       AND (p_responsible_team IS NULL OR ad_responsible_team = p_responsible_team)
       AND (p_from IS NULL OR adh_timestamp >= p_from)
       AND (p_to IS NULL OR adh_timestamp < p_to)
  ORDER BY adh_id DESC
     LIMIT p_alert_limit)
     UNION ALL
    -- and include changed checks
   (SELECT cdh_id,
           cdh_timestamp,
           cdh_action,
           cdh_row_data,
           cdh_changed_fields,
           cdh_user_name,
           cdh_check_definition_id,
           'CHECK_DEFINITION'::history_type
      FROM zzm_data.check_definition_history
      JOIN zzm_data.alert_definition
        ON cdh_check_definition_id = ad_check_definition_id
     WHERE ad_status = 'ACTIVE'
       AND ad_team = p_team
       AND (p_responsible_team IS NULL OR ad_responsible_team = p_responsible_team)
       AND (p_from IS NULL OR cdh_timestamp >= p_from)
       AND (p_to IS NULL OR cdh_timestamp < p_to)
  ORDER BY cdh_id DESC
     LIMIT p_check_limit)
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;
