RESET role;

CREATE OR REPLACE FUNCTION monitor_index_scans(OUT index_name text, OUT total_index_scans bigint) RETURNS SETOF record AS $$
    select indexrelname::text AS "indexname", idx_scan AS "total_index_scans" from pg_stat_user_indexes i where true != ( select indisunique from pg_index ii where ii.indexrelid = i.indexrelid );
$$ LANGUAGE SQL SECURITY DEFINER;
ALTER FUNCTION monitor_index_scans(OUT text, OUT bigint) OWNER TO postgres; -- need super user to see all user indexes

GRANT EXECUTE ON FUNCTION monitor_index_scans(OUT text, OUT bigint) TO public;
