CREATE OR REPLACE FUNCTION get_all_tags (
) RETURNS SETOF text AS
$BODY$
    SELECT DISTINCT unnest(adt_tags)
      FROM zzm_data.alert_definition_tree
     WHERE adt_tags IS NOT NULL;
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;
