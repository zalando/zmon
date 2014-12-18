 CREATE TYPE history_entry AS (
    id                  bigint,
    "timestamp"         timestamptz,
    "action"            zzm_data.history_action,
    row_data            hstore,
    changed_fields      hstore,
    user_name           text,
    record_id           int,
    history_type        history_type
);
