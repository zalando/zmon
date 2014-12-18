CREATE TABLE zzm_data.alert_comment (
    ac_id                          serial          NOT NULL    PRIMARY KEY,
    ac_created                     timestamptz     NOT NULL    DEFAULT now(),
    ac_created_by                  text            NOT NULL,
    ac_last_modified               timestamptz     NOT NULL    DEFAULT now(),
    ac_last_modified_by            text            NOT NULL,
    ac_comment                     text            NOT NULL,
    ac_alert_definition_id         int             NOT NULL,
    ac_entity_id                   text            NULL        CHECK (ac_entity_id ~'^[a-zA-Z0-9:_-]+$') ,
    FOREIGN KEY (ac_alert_definition_id) REFERENCES zzm_data.alert_definition_tree (adt_id)
);