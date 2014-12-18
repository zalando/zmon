-- integration test schema cleanup script
-- should NOT be run outside of Maven integration tests!
RESET ROLE;
DO $$
DECLARE
schema_name text;
BEGIN
FOR schema_name IN select nspname FROM pg_namespace WHERE nspname NOT LIKE ALL ( ARRAY['pg%', 'public', 'information_schema']) AND nspname LIKE 'z%'
LOOP
    EXECUTE 'DROP SCHEMA ' || quote_ident( schema_name ) || ' CASCADE;';
END LOOP;
END;$$;
