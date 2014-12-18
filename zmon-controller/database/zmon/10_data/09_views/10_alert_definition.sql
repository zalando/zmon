CREATE OR REPLACE RECURSIVE VIEW zzm_data.alert_definition (
    ad_id,
    ad_created,
    ad_created_by,
    ad_last_modified,
    ad_last_modified_by,
    ad_template,
    ad_parent_id,
    ad_name,
    ad_description,
    ad_team,
    ad_responsible_team,
    ad_entities,
    ad_condition,
    ad_notifications,
    ad_status,
    ad_priority,
    ad_period,
    ad_check_definition_id,
    ad_parameters,
    ad_tags,
    ad_entities_exclude
) AS
   SELECT adt_id,
          adt_created,
          adt_created_by,
          adt_last_modified,
          adt_last_modified_by,
          adt_template,
          adt_parent_id,
          adt_name,
          adt_description,
          adt_team,
          adt_responsible_team,
          adt_entities,
          adt_condition,
          adt_notifications,
          adt_status,
          adt_priority,
          adt_period,
          adt_check_definition_id,
          adt_parameters,
          adt_tags,
          adt_entities_exclude
     FROM zzm_data.alert_definition_tree
    WHERE adt_parent_id IS NULL
UNION ALL
   SELECT adt_id,
          adt_created,
          adt_created_by,
          adt_last_modified,
          adt_last_modified_by,
          adt_template,
          adt_parent_id,
          COALESCE(adt.adt_name,                 ad.ad_name),
          COALESCE(adt.adt_description,          ad.ad_description),
          COALESCE(adt.adt_team,                 ad.ad_team),
          COALESCE(adt.adt_responsible_team,     ad.ad_responsible_team),
          COALESCE(adt.adt_entities,             ad.ad_entities),
          COALESCE(adt.adt_condition,            ad.ad_condition),
          COALESCE(adt.adt_notifications,        ad.ad_notifications),
          COALESCE(adt.adt_status,               ad.ad_status),
          COALESCE(adt.adt_priority,             ad.ad_priority),
          COALESCE(adt.adt_period,               ad.ad_period),
          COALESCE(adt.adt_check_definition_id,  ad.ad_check_definition_id),
          CASE WHEN adt.adt_parameters IS NULL
            THEN ad.ad_parameters
            ELSE COALESCE(ad.ad_parameters, hstore(array[]::varchar[])) || adt.adt_parameters
          END,
          COALESCE(adt.adt_tags,                 ad.ad_tags),
          COALESCE(adt.adt_entities_exclude,     ad.ad_entities_exclude)
     FROM zzm_data.alert_definition_tree adt
     JOIN alert_definition ad
       ON adt.adt_parent_id = ad.ad_id;
