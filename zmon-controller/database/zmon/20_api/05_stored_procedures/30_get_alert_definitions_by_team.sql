CREATE OR REPLACE FUNCTION get_alert_definitions_by_team(
     IN status              zzm_data.definition_status,
     IN teams               text[]
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
         WHERE (status IS NULL OR ad_status = status)
           AND (
                (ad_team ILIKE ANY (teams))
                OR
                (ad_responsible_team ILIKE ANY (teams))
               );
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
