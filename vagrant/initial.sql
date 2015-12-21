DO
$do$
BEGIN

IF NOT EXISTS (SELECT 1 FROM zzm_data.check_definition) THEN
    INSERT INTO zzm_data.check_definition (cd_name, cd_description, cd_interval, cd_command, cd_entities, cd_owning_team, cd_status, cd_created_by, cd_last_modified_by)
    VALUES ('Random', 'Test', 10, 'normalvariate(50, 20)', '{"\"type\"=>\"GLOBAL\""}', 'Example Team', 'ACTIVE', 'Vagrant setup.sh', 'Vagrant setup.sh');
END IF;

IF NOT EXISTS (SELECT 1 FROM zzm_data.alert_definition_tree) THEN
    INSERT INTO zzm_data.alert_definition_tree (adt_created_by, adt_last_modified_by, adt_team, adt_responsible_team, adt_status, adt_name, adt_condition, adt_priority, adt_check_definition_id)
    VALUES ('Vagrant setup.sh', 'Vagrant setup.sh', 'Example Team', 'Example Team', 'ACTIVE', 'Example Alert', '> 10', 1, 1);
END IF;

IF NOT EXISTS (SELECT 1 FROM zzm_data.dashboard) THEN
    INSERT INTO zzm_data.dashboard (d_name, d_created_by, d_last_modified_by, d_widget_configuration, d_alert_teams)
    VALUES ('Example Dashboard', 'Vagrant setup.sh', 'Vagrant setup.sh', '[]', ARRAY['*']);
END IF;

END
$do$
