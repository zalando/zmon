CREATE OR REPLACE FUNCTION get_check_definitions_diff(
     IN last_snapshot_id    bigint,
    OUT snapshot_id         bigint,
    OUT check_definitions   check_definition_type[]
) AS
$BODY$
BEGIN
    SELECT MAX(cdh_id)
      INTO snapshot_id
      FROM zzm_data.check_definition_history;

    SELECT array_agg((
           h.cdh_check_definition_id,
           c.cd_name,
           c.cd_description,
           c.cd_technical_details,
           c.cd_potential_analysis,
           c.cd_potential_impact,
           c.cd_potential_solution,
           c.cd_owning_team,
           c.cd_entities,
           c.cd_interval,
           c.cd_command,
           c.cd_status,
           c.cd_source_url,
           c.cd_last_modified_by)::check_definition_type)
      INTO check_definitions
      FROM (
                SELECT DISTINCT cdh_check_definition_id
                           FROM zzm_data.check_definition_history
                          WHERE (last_snapshot_id IS NULL OR cdh_id > last_snapshot_id)
                            AND snapshot_id IS NOT NULL
            ) h
  LEFT JOIN zzm_data.check_definition c ON (c.cd_id = h.cdh_check_definition_id);
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
