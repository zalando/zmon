RESET role;

CREATE OR REPLACE FUNCTION monitor_index_bloat(OUT text, OUT float) AS $$
SELECT current_database()::text, sum(wastedibytes) FROM zz_utils.index_bloat_with_alter_statement;
$$ LANGUAGE SQL SECURITY DEFINER;
ALTER FUNCTION monitor_index_bloat(OUT text, OUT float) OWNER TO postgres; -- need super user to see bloat for all db objects

GRANT EXECUTE ON FUNCTION monitor_index_bloat(OUT text, OUT float) TO public;
