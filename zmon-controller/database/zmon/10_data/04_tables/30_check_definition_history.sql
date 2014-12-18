CREATE TABLE zzm_data.check_definition_history (
    cdh_id                  bigserial               NOT NULL PRIMARY KEY,
    cdh_timestamp           timestamptz             NOT NULL DEFAULT now(),
    cdh_action              zzm_data.history_action NOT NULL,
    cdh_row_data            hstore                  NOT NULL,
    cdh_changed_fields      hstore                  NULL,
    cdh_user_name           text                    NOT NULL,
    cdh_query               text                    NOT NULL,
    cdh_check_definition_id int                     NOT NULL
);