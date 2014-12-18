CREATE OR REPLACE FUNCTION zz_utils.get_table_data(p_table regclass)
 RETURNS text
 LANGUAGE plpgsql
 STABLE
AS $function$
/* --test
  select * from zz_utils.get_table_data('zz_commons.appdomain');
  vapply:
  psql_partner01_release -A -t -c "select * from zz_utils.get_table_data('zz_commons.appdomain');" 2>/dev/null|psql
*/
DECLARE
  l_create_temp_table_sql text;
  l_data_sql text;
  l_table_data text;
  l_update_sql text;
  l_insert_sql text;
BEGIN
  select 'create temporary table t (' || string_agg( attname || ' ' || format_type(atttypid, atttypmod) , ', ' order by attnum ) || ');',
         -- select query builder
         'select ' ||
           $header$E'insert into t values\n' || string_agg( '(' || $header$ ||
           string_agg( 'quote_nullable(' || attname || ')',
                       $delim$ || ',' || $delim$
                       order by attnum
                     ) ||
           $footer$ || ')', E',\n' ) || ';'$footer$ ||
         ' from ' || attrelid::regclass::text || ';',
         -- update statement
         'update ' || attrelid::regclass::text ||E' n \nset'||
           E'\n   ' || string_agg( attname || ' = t.' || attname, E',\n   ' order by attnum ) ||
           E'\nfrom t where\n'||'n.'||(array_agg(attname))[1]||' = t.'||(array_agg(attname))[1]||
           E'\nand ('||string_agg( 'n.'||attname  || ' is distinct FROM t.'|| attname, E'\n   OR ')||');',
         -- insert statement
         'insert into '||attrelid::regclass|| '('||string_agg(attname, ',')||')'||
         E'\nselect '||string_agg(attname, ',')||E'\nfrom t'||
         E'\nwhere t.'||(array_agg(attname))[1]||' not in (select '||(array_agg(attname))[1]||' from '||attrelid::regclass::text||');'
    into l_create_temp_table_sql,
         l_data_sql,
         l_update_sql,
         l_insert_sql
    from pg_attribute
   where attrelid = p_table::oid
     and attnum > 0
     and not attisdropped
   group by attrelid;

   execute l_data_sql into l_table_data;

   return array_to_string(ARRAY[
     'BEGIN;',
     l_create_temp_table_sql,
     l_table_data,
     l_update_sql,
     l_insert_sql,
     'COMMIT;'
   ], E'\n\n');

END;
$function$;
