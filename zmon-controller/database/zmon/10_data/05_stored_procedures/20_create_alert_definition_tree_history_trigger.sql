CREATE OR REPLACE FUNCTION zzm_data.create_alert_definition_tree_history_trigger() RETURNS trigger AS
$BODY$
DECLARE
    l_alert_definition_id   int;
    l_history_action        zzm_data.history_action;
    l_row_data              hstore;
    l_changed_fields        hstore;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        l_alert_definition_id = NEW.adt_id;
        l_history_action = 'INSERT';
        l_row_data = hstore(NEW.*);
    ELSE
        l_alert_definition_id = OLD.adt_id;
        l_row_data = hstore(OLD.*);

        IF (TG_OP = 'UPDATE') THEN
            l_history_action = 'UPDATE';
            l_changed_fields = hstore(NEW.*) - l_row_data;
        ELSE
            l_history_action = 'DELETE';
        END IF;
    END IF;

    INSERT INTO zzm_data.alert_definition_history (
                    adh_action,
                    adh_row_data,
                    adh_changed_fields,
                    adh_user_name,
                    adh_query,
                    adh_alert_definition_id
                )
         VALUES (
                    l_history_action,
                    l_row_data,
                    l_changed_fields,
                    session_user::text,
                    current_query(),
                    l_alert_definition_id
                );

    RETURN NULL;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
