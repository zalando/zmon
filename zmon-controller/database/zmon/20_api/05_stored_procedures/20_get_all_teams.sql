CREATE OR REPLACE FUNCTION get_all_teams (
) RETURNS SETOF text AS
$BODY$
    SELECT ad_team
      FROM zzm_data.alert_definition
     WHERE ad_team IS NOT NULL
     UNION
    SELECT ad_responsible_team
      FROM zzm_data.alert_definition
     WHERE ad_responsible_team IS NOT NULL
     UNION
    SELECT cd_owning_team
      FROM zzm_data.check_definition
     WHERE cd_owning_team IS NOT NULL;
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;
