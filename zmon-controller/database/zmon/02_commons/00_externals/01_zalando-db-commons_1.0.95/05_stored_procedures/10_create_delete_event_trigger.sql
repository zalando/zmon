CREATE OR REPLACE FUNCTION zz_commons.create_delete_event_trigger(p_table regclass, p_attrs text[])
RETURNS void AS
$BODY$
/*
Description
We need exactly one tupel of attribute names to rely on.
The decision on which data the consumer can rely on should be made explicitly
We check whether these attribute are part of a unique and not partial index
The values of each provided columns are stored separately in a column. Due to
PGQ structure we are limited to 5 columns. We expect this should be enough,
since mostly a primary key is used. BI stores the shared id and the primary key.

For each table a separate queue will be created.

select zz_commons.create_delete_event_trigger('schema.table'::regclass);

$Id$
$HeadURL$
*/
DECLARE
  l_insert_event    text;
  l_funcname        text;
  l_functext        text;
  l_indexoid        integer;
  l_queue           text;
  l_table_name      text;
  l_table_schema    text;
  l_trigger         text;
  l_type            text;
BEGIN
  IF p_table IS NULL OR p_attrs IS NULL THEN
    RAISE EXCEPTION 'both parameters are required';
  END IF;

  PERFORM 1 FROM (
    SELECT array_agg( pg_get_indexdef(a.indexrelid, a.attidx +1 , true)) indcols
      FROM (
        SELECT indexrelid, generate_subscripts(indkey::int[],1) attidx from pg_index
         WHERE indrelid = p_table
           AND indisunique      -- deleted row should to be identified
           AND indpred is null  -- no partial index allowed
      ) as a
     GROUP BY indexrelid
    ) as b
   WHERE p_attrs @> b.indcols AND b.indcols @> p_attrs;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'No unique index with given set of columns found!';
  END IF;

  SELECT relname, nspname
    INTO l_table_name, l_table_schema
    FROM pg_class cl
    JOIN pg_namespace ns on ns.oid = cl.relnamespace
   WHERE cl.oid = p_table;

  IF length(l_table_name) <> length(quote_ident(l_table_name))
     OR length(l_table_schema) <> length(quote_ident(l_table_schema)) THEN
    RAISE EXCEPTION 'Quoted Identifier are currently not supported';
  END IF;

  l_funcname := 'trigger_' ||l_table_name|| '_delete_event';
  l_queue    := l_table_name || '_queue';

  IF COALESCE(array_upper(p_attrs, 1), 0) = 1 THEN
    l_insert_event := $$PERFORM pgq.insert_event('$$|| l_queue ||$$', TG_OP, OLD.$$|| p_attrs[1] ||$$::text);$$;
  ELSIF COALESCE(array_upper(p_attrs, 1), 0) <= 5 THEN
    l_insert_event := $$PERFORM pgq.insert_event('$$|| l_queue ||$$', TG_OP$$;
    FOR i IN 1 .. 5 LOOP
      l_insert_event := l_insert_event || ', ' || COALESCE('OLD.'||p_attrs[i]||'::text', 'NULL');
    END LOOP;
    l_insert_event := l_insert_event || ');';
  ELSE
    RAISE EXCEPTION 'More than 5 index member not supported';
  END IF;

  l_functext := $$CREATE FUNCTION $$|| l_table_schema ||$$.$$ ||l_funcname||$$()
  RETURNS trigger AS
  $GENFUNC$
  BEGIN
    IF (TG_OP = 'DELETE') THEN
      $$|| l_insert_event ||$$
    END IF;
    RETURN NULL;
  END
  $GENFUNC$
  language 'plpgsql' SECURITY DEFINER$$;

  l_trigger := $$CREATE TRIGGER $$ || l_funcname||$$
    AFTER DELETE ON $$||l_table_schema||'.'||l_table_name||$$
    FOR EACH ROW
    execute procedure $$||l_table_schema||'.'||l_funcname||'()';

  -- missing queue would throw an exception if function is called
  -- it's not an error it the queue exists already
  PERFORM 1 FROM pgq.create_queue(l_queue);

  EXECUTE l_functext;

  EXECUTE l_trigger;
END;
$BODY$
language 'plpgsql';

COMMENT ON FUNCTION zz_commons.create_delete_event_trigger( regclass, text[]) IS
$$This function creates a trigger which generates delete events of the given table, if there
not yet another trigger exists. Name of trigger is build based on convention
'trigger_tablename_delete_event'
Since it may be used in deploy process, it will raise an exception in any error case.$$;
