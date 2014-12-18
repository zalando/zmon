CREATE TRIGGER alert_definition_tree_history_trigger
AFTER INSERT OR UPDATE OR DELETE ON zzm_data.alert_definition_tree
    FOR EACH ROW EXECUTE PROCEDURE zzm_data.create_alert_definition_tree_history_trigger();