CREATE OR REPLACE FUNCTION zz_commons.create_last_modified_trigger(table_name regclass)
  RETURNS void AS
$BODY$
/*
This function creates a trigger on the last_modified column of the given table, if there
not yet another trigger function exists. Name of trigger is build based on convention
'trigger_tablename_last_modified'
Since it may be used in deploy process, it will raise an exception in any error case.

select zz_commons.create_last_modified_trigger('schema.table'::regclass);

$Id$
$HeadURL$
*/
DECLARE
  l_colname text;
  l_funcname text;
  l_functext text;
  l_table_name text;
  l_schema_name text;
  l_type text;
  l_trigger text;
  l_assignment text;
BEGIN
  IF table_name IS NULL THEN
    RAISE EXCEPTION 'Tablename is required';
  END IF;

  SELECT ns.nspname, cl.relname
    INTO l_schema_name, l_table_name
    FROM pg_catalog.pg_class cl
    JOIN pg_namespace ns on cl.relnamespace = ns.oid
   WHERE cl.oid = table_name::oid;

  IF length(l_table_name) <> length(quote_ident(l_table_name))
     OR length(l_schema_name) <> length(quote_ident(l_schema_name)) THEN
    RAISE EXCEPTION 'Quoted Identifier are currently not supported';
  END IF;

  SELECT attname, typname INTO l_colname, l_type
    FROM pg_attribute
    JOIN pg_type pt on atttypid = pt.oid
   WHERE attrelid = table_name::oid
     AND attname LIKE '%last_modified'
     AND attisdropped = false
     AND attnum > 0 -- is regular column
     AND (typname = 'timestamp' OR typname = 'timestamptz');

  IF NOT FOUND OR l_colname IS NULL THEN
    RAISE EXCEPTION  'No last_modified column found';
  END IF;

  l_funcname := 'trigger_' ||l_table_name|| '_last_modified';

  IF l_type = 'timestamp' THEN
    l_assignment := $$NEW.$$||l_colname||$$ := clock_timestamp()::timestamp;$$;
  ELSE
    l_assignment := $$NEW.$$||l_colname||$$ := clock_timestamp();$$;
  END IF;

  l_functext := $$CREATE FUNCTION $$|| l_schema_name ||$$.$$ ||l_funcname||$$()
  RETURNS trigger AS
  $GENFUNC$
  BEGIN
    IF (TG_OP = 'UPDATE') THEN
      IF NOT NEW.$$||l_colname||$$ IS DISTINCT FROM OLD.$$||l_colname||$$ THEN
        $$||l_assignment||$$
      END IF;
      RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
      RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
      RETURN NEW;
    END IF;
  END
  $GENFUNC$
  language 'plpgsql'$$;

  l_trigger := $$CREATE TRIGGER $$ || l_funcname||$$
    BEFORE UPDATE ON $$||l_schema_name||'.'||l_table_name||$$
    FOR EACH ROW WHEN ( NEW is distinct from OLD )
    execute procedure $$||l_schema_name||'.'||l_funcname||'()';

  EXECUTE l_functext;

  EXECUTE l_trigger;

END;
$BODY$
language 'plpgsql';

COMMENT ON FUNCTION zz_commons.create_last_modified_trigger( regclass) IS
$$This function creates a trigger on the last_modified column of the given table, if there
not yet another trigger exists. Name of trigger is build based on convention
'trigger_tablename_last_modified'
Since it may be used in deploy process, it will raise an exception in any error case.$$;

