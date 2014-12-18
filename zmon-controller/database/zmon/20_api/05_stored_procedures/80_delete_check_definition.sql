CREATE OR REPLACE FUNCTION delete_check_definition (
     IN p_user_name   text,
     IN p_name        text,
     IN p_owning_team text,
    OUT p_check_definition check_definition_type
) AS
$BODY$
DECLARE
    l_updated_alerts_count int;
BEGIN

     -- set check as deleted
     UPDATE zzm_data.check_definition
        SET cd_status           = 'DELETED',
            cd_last_modified_by = p_user_name,
            cd_last_modified    = now()
      WHERE cd_name = p_name
        AND cd_owning_team = p_owning_team
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
            cd_last_modified_by
       INTO p_check_definition;

       --  recursively set all alerts as deleted
       WITH RECURSIVE tree AS (
         SELECT adt_id
           FROM zzm_data.alert_definition_tree
          WHERE adt_check_definition_id = p_check_definition.id
      UNION ALL
         SELECT adt.adt_id
           FROM zzm_data.alert_definition_tree adt
           JOIN tree t
             ON adt.adt_parent_id = t.adt_id
       )
     UPDATE zzm_data.alert_definition_tree adt
        SET adt_status           = 'DELETED',
            adt_last_modified_by = p_user_name,
            adt_last_modified    = now()
       FROM tree t
      WHERE adt.adt_id = t.adt_id
        AND adt_status <> 'DELETED';
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
