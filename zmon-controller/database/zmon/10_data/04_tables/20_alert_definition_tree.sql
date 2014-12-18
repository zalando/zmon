CREATE TABLE zzm_data.alert_definition_tree   (
    adt_id                          serial                       NOT NULL    PRIMARY KEY,
    adt_created                     timestamptz                  NOT NULL    DEFAULT now(),
    adt_created_by                  text                         NOT NULL,
    adt_last_modified               timestamptz                  NOT NULL    DEFAULT now(),
    adt_last_modified_by            text                         NOT NULL,
    adt_template                    boolean                      NOT NULL    DEFAULT FALSE,
    adt_team                        varchar(256)                 NOT NULL    CHECK ( adt_team = btrim(adt_team) ),
    adt_responsible_team            varchar(256)                 NOT NULL    CHECK ( adt_responsible_team = btrim(adt_responsible_team) ),
    adt_status                      zzm_data.definition_status   NOT NULL,
    adt_parent_id                   int                          NULL,
    adt_name                        varchar(256)                 NULL        CHECK ( adt_name = btrim(adt_name) ),
    adt_description                 text                         NULL,
    adt_entities                    hstore[]                     NULL,
    adt_entities_exclude            hstore[]                     NULL,
    adt_condition                   text                         NULL,
    adt_notifications               text[]                       NULL,
    adt_priority                    int                          NULL        CHECK ( adt_priority >= 1 AND adt_priority <= 3 ),
    adt_period                      text                         NULL,
    adt_check_definition_id         int                          NULL        REFERENCES zzm_data.check_definition (cd_id),
    adt_parameters                  hstore                       NULL,
    adt_tags                        text[]                       NULL
);

CREATE INDEX ON zzm_data.alert_definition_tree(adt_parent_id);
CREATE INDEX ON zzm_data.alert_definition_tree(adt_check_definition_id);

COMMENT ON COLUMN zzm_data.alert_definition_tree.adt_team IS 'The team that should see the alert';
COMMENT ON COLUMN zzm_data.alert_definition_tree.adt_responsible_team IS 'The team that should fix the alert when triggered';
