CREATE TYPE check_definition_import AS (
    name                varchar(256),
    description         text,
    technical_details   text,
    potential_analysis  text,
    potential_impact    text,
    potential_solution  text,
    owning_team         varchar(256),
    entities            hstore[],
    "interval"          int,
    command             text,
    status              zzm_data.definition_status,
    source_url          text,
    last_modified_by    text
);