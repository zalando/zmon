CREATE OR REPLACE FUNCTION validate_alert_definition_children (
     IN  p_alert_definition     alert_definition_type,
     OUT status                 operation_status,
     OUT error_message          text
) AS
$BODY$
DECLARE
    l_alert_ids int[];
BEGIN
    WITH RECURSIVE tree(
         id                  ,
         name                ,
         description         ,
         entities            ,
         entities_exclude    ,
         condition           ,
         check_definition_id ,
         priority            ,
         template            ,
         parent_id
    ) AS (
      SELECT adt_id,
             coalesce(adt_name,                 p_alert_definition.name),
             coalesce(adt_description,          p_alert_definition.description),
             coalesce(adt_entities,             p_alert_definition.entities),
             coalesce(adt_entities_exclude,     p_alert_definition.entities_exclude),
             coalesce(adt_condition,            p_alert_definition.condition),
             coalesce(adt_check_definition_id,  p_alert_definition.check_definition_id),
             coalesce(adt_priority,             p_alert_definition.priority),
             adt_template,
             adt_parent_id
        FROM zzm_data.alert_definition_tree
       WHERE adt_parent_id = p_alert_definition.id
   UNION ALL
      SELECT c.adt_id,
             coalesce(c.adt_name,                 t.name),
             coalesce(c.adt_description,          t.description),
             coalesce(c.adt_entities,             t.entities),
             coalesce(c.adt_entities_exclude,     t.entities_exclude),
             coalesce(c.adt_condition,            t.condition),
             coalesce(c.adt_check_definition_id,  t.check_definition_id),
             coalesce(c.adt_priority,             t.priority),
             c.adt_template,
             c.adt_parent_id
        FROM zzm_data.alert_definition_tree c
        JOIN tree t
          ON c.adt_parent_id = t.id)
      SELECT array_agg(id)
        INTO l_alert_ids
        FROM tree t
       WHERE template = 'f'
         -- and at least one column is null
         AND (row(t.*) = row(t.*)) IS NULL;

    IF ARRAY_LENGTH(l_alert_ids, 1) IS NOT NULL AND ARRAY_LENGTH(l_alert_ids, 1) > 0 THEN
        status := 'ALERT_DEFINITION_FIELD_MISSING';
        error_message := 'Update breaks the following alert definitions: ' || l_alert_ids::text;
    ELSE
        status := 'SUCCESS';
    END IF;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
