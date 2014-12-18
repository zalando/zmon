CREATE OR REPLACE FUNCTION get_alert_comments (
     IN p_alert_definition_id int,
     IN p_limit               int,
     IN p_offset              int
) RETURNS SETOF alert_comment AS
$BODY$
    SELECT ac_id,
           ac_created,
           ac_created_by,
           ac_last_modified,
           ac_last_modified_by,
           ac_comment,
           ac_alert_definition_id,
           ac_entity_id
      FROM zzm_data.alert_comment
     WHERE ac_alert_definition_id = p_alert_definition_id
  ORDER BY ac_last_modified DESC, ac_id DESC
     LIMIT p_limit
    OFFSET p_offset;
$BODY$
LANGUAGE SQL VOLATILE SECURITY DEFINER
COST 100;