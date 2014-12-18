CREATE OR REPLACE FUNCTION delete_detached_check_definitions (
) RETURNS SETOF check_definition_type AS
$BODY$
BEGIN
    RETURN QUERY
       DELETE
         FROM zzm_data.check_definition
        WHERE cd_status = 'DELETED'
          AND NOT EXISTS (SELECT 1
                            FROM zzm_data.alert_definition
                           WHERE ad_check_definition_id = cd_id)
    RETURNING cd_id,
              cd_name,
              cd_description,
              cd_technical_details,
              cd_potential_analysis,
              cd_potential_impact,
              cd_potential_solution,
              cd_owning_team,
              cd_entities,
              cd_interval,
              cd_command,
              cd_status,
              cd_source_url,
              cd_last_modified_by;
END;
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
