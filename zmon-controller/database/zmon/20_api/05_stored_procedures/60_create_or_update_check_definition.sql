CREATE OR REPLACE FUNCTION create_or_update_check_definition (
     IN check_definition_import check_definition_import,
     OUT entity                 check_definition_type,
     OUT new_entity             boolean
) AS
$BODY$
BEGIN
    entity.name                 = check_definition_import.name;
    entity.description          = check_definition_import.description;
    entity.technical_details    = check_definition_import.technical_details;
    entity.potential_analysis   = check_definition_import.potential_analysis;
    entity.potential_impact     = check_definition_import.potential_impact;
    entity.potential_solution   = check_definition_import.potential_solution;
    entity.owning_team          = check_definition_import.owning_team;
    entity.entities             = check_definition_import.entities;
    entity.interval             = check_definition_import.interval;
    entity.command              = check_definition_import.command;
    entity.status               = check_definition_import.status;
    entity.source_url           = check_definition_import.source_url;
    entity.last_modified_by     = check_definition_import.last_modified_by;

    new_entity := FALSE;

    UPDATE zzm_data.check_definition
       SET cd_name                 = check_definition_import.name,
           cd_description          = check_definition_import.description,
           cd_technical_details    = check_definition_import.technical_details,
           cd_potential_analysis   = check_definition_import.potential_analysis,
           cd_potential_impact     = check_definition_import.potential_impact,
           cd_potential_solution   = check_definition_import.potential_solution,
           cd_owning_team          = check_definition_import.owning_team,
           cd_entities             = check_definition_import.entities,
           cd_interval             = check_definition_import.interval,
           cd_command              = check_definition_import.command,
           cd_status               = check_definition_import.status,
           cd_source_url           = check_definition_import.source_url,
           cd_last_modified_by     = check_definition_import.last_modified_by,
           cd_last_modified        = now()
     WHERE lower(cd_source_url)    = lower(check_definition_import.source_url)
        OR lower(cd_name)          = lower(check_definition_import.name)
       AND lower(cd_owning_team)   = lower(check_definition_import.owning_team)
 RETURNING cd_id INTO entity.id;

    IF NOT FOUND THEN

        -- if it's not there, we should create a new one
        INSERT INTO zzm_data.check_definition (
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
            cd_created_by,
            cd_last_modified_by
        )
        VALUES (
            check_definition_import.name,
            check_definition_import.description,
            check_definition_import.technical_details,
            check_definition_import.potential_analysis,
            check_definition_import.potential_impact,
            check_definition_import.potential_solution,
            check_definition_import.owning_team,
            check_definition_import.entities,
            check_definition_import.interval,
            check_definition_import.command,
            check_definition_import.status,
            check_definition_import.source_url,
            check_definition_import.last_modified_by,
            check_definition_import.last_modified_by
        ) RETURNING cd_id INTO entity.id;

        new_entity := TRUE;
    END IF;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
