CREATE TABLE zzm_data.dashboard (
    d_id                      serial                NOT NULL    PRIMARY KEY,
    d_name                    text                  NOT NULL,
    d_created                 timestamptz           NOT NULL    DEFAULT now(),
    d_created_by              text                  NOT NULL,
    d_last_modified           timestamptz           NOT NULL    DEFAULT now(),
    d_last_modified_by        text                  NOT NULL,
    d_widget_configuration    json                  NOT NULL,
    d_alert_teams             text[]                NULL    ,
    d_view_mode               zzm_data.view_mode    NOT NULL    DEFAULT 'FULL',
    d_edit_option             zzm_data.edit_option  NOT NULL    DEFAULT 'PRIVATE',
    d_shared_teams            text[]                NOT NULL    DEFAULT '{}',
    d_tags                    text[]                NULL
);
