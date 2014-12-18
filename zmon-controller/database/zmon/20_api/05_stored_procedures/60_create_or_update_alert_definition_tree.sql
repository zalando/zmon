CREATE OR REPLACE FUNCTION create_or_update_alert_definition_tree (
     IN  p_alert_definition     alert_definition_type,
     OUT status                 operation_status,
     OUT error_message          text,
     OUT entity                 alert_definition_type
) AS
$BODY$
DECLARE
    l_check_definiton_status zzm_data.definition_status;
    l_merged_entity          alert_definition_type;
BEGIN
    -- validate entity

    -- prevent circular references
    IF p_alert_definition.parent_id IS NOT NULL THEN
        PERFORM 1
           FROM zzm_data.alert_definition_tree
          WHERE adt_id = p_alert_definition.parent_id
          limit 1;

            -- if the parent doesn't exist, return an error
             IF NOT FOUND THEN
                status := 'ALERT_DEFINITION_NOT_FOUND';
                error_message := 'Parent alert definition with id ' || p_alert_definition.parent_id || ' not found';
                RETURN;
            END IF;
    END IF;

    -- validate mandatory fields
    l_merged_entity := p_alert_definition;
    IF l_merged_entity.parent_id IS NOT NULL THEN
        SELECT coalesce(l_merged_entity.name, ad_name),
               coalesce(l_merged_entity.description, ad_description),
               coalesce(l_merged_entity.entities, ad_entities),
               coalesce(l_merged_entity.entities_exclude, ad_entities_exclude),
               coalesce(l_merged_entity.condition, ad_condition),
               coalesce(l_merged_entity.check_definition_id, ad_check_definition_id),
               coalesce(l_merged_entity.priority, ad_priority)
          FROM zzm_data.alert_definition
          INTO l_merged_entity.name,
               l_merged_entity.description,
               l_merged_entity.entities,
               l_merged_entity.entities_exclude,
               l_merged_entity.condition,
               l_merged_entity.check_definition_id,
               l_merged_entity.priority
         WHERE ad_id = l_merged_entity.parent_id;
    END IF;

    -- TODO fix concurrency issues
    IF l_merged_entity.check_definition_id IS NULL THEN
        status = 'ALERT_DEFINITION_FIELD_MISSING';
        error_message := 'check definition id is mandatory';
        RETURN;
    END IF;

    IF l_merged_entity.template = 'f' THEN
        IF l_merged_entity.name IS NULL THEN
            status = 'ALERT_DEFINITION_FIELD_MISSING';
            error_message := 'name is mandatory';
            RETURN;
        ELSIF l_merged_entity.description IS NULL THEN
            status = 'ALERT_DEFINITION_FIELD_MISSING';
            error_message := 'description is mandatory';
            RETURN;
        ELSIF l_merged_entity.entities IS NULL THEN
            status = 'ALERT_DEFINITION_FIELD_MISSING';
            error_message := 'entities filter is mandatory';
            RETURN;
        ELSIF l_merged_entity.entities_exclude IS NULL THEN
          status = 'ALERT_DEFINITION_FIELD_MISSING';
          error_message := 'exclude entities filter is mandatory';
          RETURN;
        ELSIF l_merged_entity.condition IS NULL THEN
            status = 'ALERT_DEFINITION_FIELD_MISSING';
            error_message := 'condition is mandatory';
            RETURN;
        ELSIF l_merged_entity.priority IS NULL THEN
            status = 'ALERT_DEFINITION_FIELD_MISSING';
            error_message := 'priority is mandatory';
            RETURN;
        END IF;
    END IF;

    SELECT v.status,
           v.error_message
      FROM validate_alert_definition_children(l_merged_entity) v
      INTO status,
           error_message;

     IF status <> 'SUCCESS' THEN
        RETURN;
     END IF;

    -- create entity
    entity := p_alert_definition;
    IF p_alert_definition.id IS NOT NULL THEN
        UPDATE zzm_data.alert_definition_tree
           SET adt_name                 = p_alert_definition.name,
               adt_description          = p_alert_definition.description,
               adt_priority             = p_alert_definition.priority,
               adt_team                 = p_alert_definition.team,
               adt_responsible_team     = p_alert_definition.responsible_team,
               adt_entities             = p_alert_definition.entities,
               adt_entities_exclude     = p_alert_definition.entities_exclude,
               adt_condition            = p_alert_definition.condition,
               adt_notifications        = p_alert_definition.notifications,
               adt_status               = p_alert_definition.status,
               adt_last_modified_by     = p_alert_definition.last_modified_by,
               adt_period               = p_alert_definition.period,
               adt_template             = p_alert_definition.template,
               adt_last_modified        = now(),
               adt_parameters           = p_alert_definition.parameters,
               adt_tags                 = p_alert_definition.tags
          FROM zzm_data.alert_definition
         WHERE adt_id = ad_id
           AND adt_id = p_alert_definition.id
           -- Updates to 'DELETED' alerts are not allowed
           AND ad_status <> 'DELETED'
     RETURNING adt_last_modified
          INTO entity.last_modified;

         IF NOT FOUND THEN
            status := 'ALERT_DEFINITION_NOT_FOUND';
            error_message := 'Alert definition with id ' || p_alert_definition.id || ' is not available for edition';
            RETURN;
         END IF;
    ELSE
        SELECT cd_status
          FROM zzm_data.check_definition
          INTO l_check_definiton_status
          -- use merged check_definition since it can be inherited
         WHERE cd_id = l_merged_entity.check_definition_id FOR SHARE;

        IF l_check_definiton_status IS NULL OR l_check_definiton_status <> 'ACTIVE' THEN
            status := 'CHECK_DEFINITION_NOT_ACTIVE';
            error_message := 'Check definition with id ' || p_alert_definition.check_definition_id || ' is not active';
            RETURN;
        END IF;

        INSERT INTO zzm_data.alert_definition_tree (
            adt_name,
            adt_description,
            adt_priority,
            adt_check_definition_id,
            adt_team,
            adt_responsible_team,
            adt_entities,
            adt_entities_exclude,
            adt_condition,
            adt_notifications,
            adt_status,
            adt_created_by,
            adt_last_modified_by,
            adt_period,
            adt_template,
            adt_parent_id,
            adt_parameters,
            adt_tags
        )
        VALUES (
            p_alert_definition.name,
            p_alert_definition.description,
            p_alert_definition.priority,
            p_alert_definition.check_definition_id,
            p_alert_definition.team,
            p_alert_definition.responsible_team,
            p_alert_definition.entities,
            p_alert_definition.entities_exclude,
            p_alert_definition.condition,
            p_alert_definition.notifications,
            p_alert_definition.status,
            p_alert_definition.last_modified_by,
            p_alert_definition.last_modified_by,
            p_alert_definition.period,
            p_alert_definition.template,
            p_alert_definition.parent_id,
            p_alert_definition.parameters,
            p_alert_definition.tags
        ) RETURNING
            adt_id,
            adt_last_modified
          INTO
            entity.id,
            entity.last_modified;
    END IF;

    status := 'SUCCESS';
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;
