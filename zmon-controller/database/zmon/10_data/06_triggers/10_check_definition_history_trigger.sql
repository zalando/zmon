CREATE TRIGGER check_definition_history_trigger
AFTER INSERT OR UPDATE OR DELETE ON zzm_data.check_definition
    FOR EACH ROW EXECUTE PROCEDURE zzm_data.create_check_definition_history_trigger();