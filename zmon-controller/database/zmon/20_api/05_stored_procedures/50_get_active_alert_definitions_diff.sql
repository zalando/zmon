CREATE OR REPLACE FUNCTION get_active_alert_definitions_diff(
    OUT snapshot_id         bigint,
    OUT alert_definitions   alert_definition_type[]
) AS
$BODY$
BEGIN
    SELECT MAX(adh_id)
      INTO snapshot_id
      FROM zzm_data.alert_definition_history;

    SELECT array_agg((
           ad_id,
           ad_name,
           ad_description,
           ad_team,
           ad_responsible_team,
           ad_entities,
           ad_entities_exclude,
           ad_condition,
           ad_notifications,
           ad_check_definition_id,
           ad_status,
           ad_priority,
           ad_last_modified,
           ad_last_modified_by,
           ad_period,
           ad_template,
           ad_parent_id,
           ad_parameters,
           ad_tags)::alert_definition_type)
      INTO alert_definitions
      FROM zzm_data.alert_definition
     WHERE ad_template = 'f'
       AND ad_status = 'ACTIVE';
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
