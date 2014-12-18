CREATE TYPE dashboard AS (
    id                      int,
    name                    text,
    created_by              text,
    last_modified           timestamptz,
    last_modified_by        text,
    widget_configuration    text,
    alert_teams             text[],
    view_mode               zzm_data.view_mode,
    edit_option             zzm_data.edit_option,
    shared_teams            text[],
    tags                    text[]
);