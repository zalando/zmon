CREATE OR REPLACE FUNCTION create_or_update_dashboard (
     IN dashboard         dashboard,
     OUT entity           dashboard,
     OUT status           operation_status,
     OUT error_message    text
) AS
$BODY$
DECLARE
    l_view_mode   zzm_data.view_mode;
    l_edit_option zzm_data.edit_option;
BEGIN
    l_view_mode   = COALESCE(dashboard.view_mode, 'FULL');
    l_edit_option = COALESCE(dashboard.edit_option, 'PRIVATE');

    IF dashboard.id IS NOT NULL THEN
        UPDATE zzm_data.dashboard
           SET d_id                     = dashboard.id,
               d_name                   = dashboard.name,
               d_last_modified          = now(),
               d_last_modified_by       = dashboard.last_modified_by,
               d_widget_configuration   = dashboard.widget_configuration::json,
               d_alert_teams            = dashboard.alert_teams,
               d_view_mode              = l_view_mode,
               d_edit_option            = l_edit_option,
               -- only update shared teams when edit option is changed to team
               d_shared_teams           = CASE WHEN d_edit_option <> l_edit_option AND l_edit_option = 'TEAM'
                                               THEN dashboard.shared_teams
                                               ELSE d_shared_teams
                                          END,
               d_tags                   = dashboard.tags
         WHERE d_id  = dashboard.id
     RETURNING d_id,
               d_name,
               d_created_by,
               d_last_modified,
               d_last_modified_by,
               d_widget_configuration,
               d_alert_teams,
               d_view_mode,
               d_edit_option,
               d_shared_teams,
               d_tags
          INTO entity.id,
               entity.name,
               entity.created_by,
               entity.last_modified,
               entity.last_modified_by,
               entity.widget_configuration,
               entity.alert_teams,
               entity.view_mode,
               entity.edit_option,
               entity.shared_teams,
               entity.tags;
    ELSE
        -- if it's not there, we should create a new one
        INSERT INTO zzm_data.dashboard (
            d_name,
            d_created_by,
            d_last_modified_by,
            d_widget_configuration,
            d_alert_teams,
            d_view_mode,
            d_edit_option,
            d_shared_teams,
            d_tags
        )
        VALUES (
            dashboard.name,
            dashboard.created_by,
            dashboard.last_modified_by,
            dashboard.widget_configuration::json,
            dashboard.alert_teams,
            l_view_mode,
            l_edit_option,
            dashboard.shared_teams,
            dashboard.tags
        )
         RETURNING d_id,
               d_name,
               d_created_by,
               d_last_modified,
               d_last_modified_by,
               d_widget_configuration,
               d_alert_teams,
               d_view_mode,
               d_edit_option,
               d_shared_teams,
               d_tags
          INTO entity.id,
               entity.name,
               entity.created_by,
               entity.last_modified,
               entity.last_modified_by,
               entity.widget_configuration,
               entity.alert_teams,
               entity.view_mode,
               entity.edit_option,
               entity.shared_teams,
               entity.tags;
    END IF;

    status := 'SUCCESS';
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
