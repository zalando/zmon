CREATE OR REPLACE FUNCTION zzm_data.create_check_definition_history_trigger() RETURNS trigger AS
$BODY$
DECLARE
    l_check_definition_id   int;
    l_history_action        zzm_data.history_action;
    l_row_data              hstore;
    l_changed_fields        hstore;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        l_check_definition_id = NEW.cd_id;
        l_history_action = 'INSERT';
        l_row_data = hstore(NEW.*);
    ELSE
        l_check_definition_id = OLD.cd_id;
        l_row_data = hstore(OLD.*);

        IF (TG_OP = 'UPDATE') THEN
            l_history_action = 'UPDATE';
            l_changed_fields = hstore(NEW.*) - l_row_data;
        ELSE
            l_history_action = 'DELETE';
        END IF;
    END IF;

    INSERT INTO zzm_data.check_definition_history (
                    cdh_action,
                    cdh_row_data,
                    cdh_changed_fields,
                    cdh_user_name,
                    cdh_query,
                    cdh_check_definition_id
                )
         VALUES (
                    l_history_action,
                    l_row_data,
                    l_changed_fields,
                    session_user::text,
                    current_query(),
                    l_check_definition_id
                );

    RETURN NULL;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
