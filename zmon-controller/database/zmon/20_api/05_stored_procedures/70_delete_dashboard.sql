CREATE OR REPLACE FUNCTION delete_dashboard(
     IN dashboard_id    int
) RETURNS VOID AS
$BODY$
BEGIN
    DELETE FROM zzm_data.dashboard
          WHERE d_id = dashboard_id;
END
$BODY$
LANGUAGE 'plpgsql' VOLATILE SECURITY DEFINER
COST 100;