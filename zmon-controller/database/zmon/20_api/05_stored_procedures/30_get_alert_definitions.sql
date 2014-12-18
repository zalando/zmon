CREATE OR REPLACE FUNCTION get_alert_definitions(
     IN status              zzm_data.definition_status,
     IN alert_ids           int[]
) RETURNS SETOF alert_definition_type AS
$BODY$
BEGIN
    RETURN QUERY
        SELECT ad_id,
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
               ad_tags
          FROM zzm_data.alert_definition
         WHERE (ad_id = ANY (alert_ids))
           AND (status IS NULL OR ad_status = status);
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;