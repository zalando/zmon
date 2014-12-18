CREATE TABLE zzm_data.check_definition (
    cd_id                          serial          NOT NULL    PRIMARY KEY,
    cd_created                     timestamptz     NOT NULL    DEFAULT now(),
    cd_created_by                  text            NOT NULL,
    cd_last_modified               timestamptz     NOT NULL    DEFAULT now(),
    cd_last_modified_by            text            NOT NULL,
    cd_name                        varchar(256)    NOT NULL    CHECK ( cd_name = btrim(cd_name) ),
    cd_description                 text            NOT NULL,
    cd_technical_details           text            NULL        DEFAULT '',
    cd_potential_analysis          text            NULL        DEFAULT '',
    cd_potential_impact            text            NULL        DEFAULT '',
    cd_potential_solution          text            NULL        DEFAULT '',
    cd_owning_team                 varchar(256)    NOT NULL    CHECK ( cd_owning_team = btrim(cd_owning_team) ),
    cd_entities                    hstore[]        NOT NULL    CHECK ( array_length(cd_entities, 1) > 0 ),
    cd_interval                    int             NOT NULL,
    cd_command                     text            NOT NULL,
    cd_source_url                  text            NULL,
    cd_status                      zzm_data.definition_status NOT NULL     DEFAULT 'ACTIVE'
);

CREATE UNIQUE INDEX ON zzm_data.check_definition (lower(cd_name), lower(cd_owning_team));
CREATE UNIQUE INDEX ON zzm_data.check_definition (lower(cd_source_url));
