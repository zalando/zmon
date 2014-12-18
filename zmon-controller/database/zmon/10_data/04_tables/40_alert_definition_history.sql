CREATE TABLE zzm_data.alert_definition_history (
    adh_id                  bigserial               NOT NULL PRIMARY KEY,
    adh_timestamp           timestamptz             NOT NULL DEFAULT now(),
    adh_action              zzm_data.history_action NOT NULL,
    adh_row_data            hstore                  NOT NULL,
    adh_changed_fields      hstore                  NULL,
    adh_user_name           text                    NOT NULL,
    adh_query               text                    NOT NULL,
    adh_alert_definition_id int                     NOT NULL
);