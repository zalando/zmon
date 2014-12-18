CREATE OR REPLACE FUNCTION get_check_definitions_by_owning_team(
     IN status       zzm_data.definition_status,
     IN owning_teams text[]
) RETURNS SETOF check_definition_type AS
$BODY$
BEGIN
  RETURN QUERY
        SELECT cd_id,
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
               cd_last_modified_by
          FROM zzm_data.check_definition
         WHERE (status IS NULL OR cd_status = status)
           AND cd_owning_team ILIKE ANY (owning_teams);
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
