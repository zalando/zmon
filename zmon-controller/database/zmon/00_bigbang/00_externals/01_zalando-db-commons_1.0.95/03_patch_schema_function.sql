-- use these functions to patch existing schemas to the current role settings
-- use arguments equivalent to zz_utils.CREATE_project_schema_(api|data)_env
-- the corresponding function for API is not included since this is always done anew by deployctl

CREATE OR REPLACE FUNCTION zz_utils.patch_project_schema_data_env(
                                schema_name text, children_schema_names text[] default null::text[]
                                , append_searchpath boolean default NULL, deprecated_schema_owner text default 'zalando'
                                , isPublic boolean default false, skipCreation boolean default true)
RETURNS VOID AS
$$
DECLARE
    _project_schema_prefix text := zz_utils.get_project_schema_prefix(schema_name) ;
    _data_user text             := _project_schema_prefix || 'user' ;
    _data_reader text           := _project_schema_prefix || 'reader' ;
    _data_reader_basic text     := _project_schema_prefix || 'reader_basic' ;
    _data_writer text           := _project_schema_prefix || 'writer' ;
    _data_owner text            := _project_schema_prefix || 'owner' ;

    obj text;
    objid int;
BEGIN
    -- simulate the creation function to establish necessary structures
    PERFORM zz_utils.create_project_schema_data_env(
                                schema_name:=schema_name, children_schema_names:=children_schema_names
                                , append_searchpath:=append_searchpath, deprecated_schema_owner:=deprecated_schema_owner
                                , isPublic:=isPublic, skipCreation:=skipCreation);

    RESET ROLE;

    -- This would generate sql statements to be injected into the respective database
    PERFORM zz_utils.change_project_schema_owner(schema_name:=schema_name, new_owner:=_data_owner);

    -- grant the necessary privileges on existing objects
    -- this is done after zz_utils.change_project_schema_owner(schema_name:=schema_name, new_owner:=_data_owner);
    -- to ensure that the owner of the object is updated before the GRANTS; this was important e.g. for granting Usage for Types
    EXECUTE('
        grant USAGE on schema ' || schema_name || ' to ' || _data_user || ' ;

        grant SELECT ON ALL SEQUENCES IN SCHEMA ' || schema_name || ' to ' || _data_reader || ' ;
        grant SELECT ON ALL TABLES IN SCHEMA ' || schema_name || ' to ' || _data_reader || ' ;
        grant REFERENCES ON ALL TABLES IN SCHEMA ' || schema_name || ' to ' || _data_reader || ' ;
        grant SELECT ON ALL SEQUENCES IN SCHEMA ' || schema_name || ' to ' || _data_reader_basic || ' ;
        grant SELECT ON ALL TABLES IN SCHEMA ' || schema_name || ' to ' || _data_reader_basic || ' ;
        grant REFERENCES ON ALL TABLES IN SCHEMA ' || schema_name || ' to ' || _data_reader_basic || ' ;

        grant USAGE ON ALL SEQUENCES IN SCHEMA ' || schema_name || ' to ' || _data_writer || ' ;
        grant EXECUTE ON ALL FUNCTIONS IN SCHEMA ' || schema_name || ' to ' || _data_writer || ' ;
        grant INSERT, DELETE, UPDATE ON ALL TABLES IN SCHEMA ' || schema_name || ' to ' || _data_writer || ' ;
   ');

END;
$$
language plpgsql;
