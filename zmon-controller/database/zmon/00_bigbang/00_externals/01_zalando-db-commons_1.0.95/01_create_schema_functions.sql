
-- role prefix scheme e.g. zalando_customer_zc_data_
CREATE OR REPLACE FUNCTION zz_utils.get_project_schema_prefix(schema_name text)
RETURNS text AS
$$
DECLARE
  _project text := regexp_replace(current_database(), E'^(zalando|prod|beta|patch|release|integration|local)_([_a-z]+)([0-9]+)?_db$', E'\\2', 'i') ; -- extract DBNAME from pre_DBNAME_db
  _schema  text := regexp_replace(schema_name, E'_r[_0-9]+', '', 'i') ; -- remove branch extensions possibly added by deployCTL
BEGIN
  IF current_database() ~* ('(zalando|local|integration|release|patch|prod)_' || _project || '[0-9]{0,2}_db')
     AND schema_name ~* (_schema || '(_r[0-9]{2}_[0-9]{2}_[0-9]{2})?')  --ensure the extraction went well
  THEN
    RETURN (SELECT 'zalando_'
             || case when schema_name IN ('zz_commons', 'zcpe_data','pgq')
                     then ''  -- no project/database-specific zz_commons, zcpe_data
                     else _project || '_'
                     end
             || case when schema_name = ''  --project/database level roles
                     then ''
                     else _schema || '_'
                     end
           ) ;
  ELSE
    RAISE INFO 'project: %, schema: %', _project, _schema;
    RAISE EXCEPTION 'Extraction of project_schema_prefix did not go well; please check database and schema names.';
  END IF;
END;
$$
language plpgsql;


-- create a role and its memberships
CREATE OR REPLACE FUNCTION zz_utils.setup_create_role(role_name text, inroles text[] default null , password text default null)
RETURNS text AS
$$
DECLARE
  l_roles text;
BEGIN

    BEGIN
        -- check if role exists
        EXECUTE 'CREATE ROLE ' || quote_ident(role_name) || COALESCE(' WITH LOGIN PASSWORD ' || quote_literal(password),'') || ' ;';

        RAISE INFO 'Role % created',  quote_ident(role_name);

        EXCEPTION WHEN SQLSTATE '42710' THEN

        RAISE INFO 'ROLE % already exists / or other error', quote_ident(role_name) USING ERRCODE = SQLSTATE, DETAIL = SQLERRM;
    END;

    SELECT string_agg ( quote_ident ( role ) ,','  ) INTO l_roles FROM unnest ( inroles ) AS t ( role );

    IF length(l_roles) > 0
    THEN
        BEGIN
            EXECUTE 'GRANT ' || l_roles || ' TO ' || quote_ident(role_name) || ';';
            RAISE INFO 'Granted roles % to %', l_roles , quote_ident(role_name);
        EXCEPTION WHEN OTHERS THEN
            RAISE INFO 'WARNING! ' USING ERRCODE=SQLSTATE, DETAIL=SQLERRM;
        END;
    END IF;

    RETURN 'role created ' || quote_ident(role_name);
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;


-- create default privileges for core data-roles
CREATE OR REPLACE FUNCTION zz_utils.create_project_schema_core_data_roles(schema_name text)
RETURNS VOID AS
$$
DECLARE
  _project_schema_prefix text := zz_utils.get_project_schema_prefix(schema_name) ;
  _project_prefix        text := zz_utils.get_project_schema_prefix('') ;
  _data_user text             := quote_ident(_project_schema_prefix || 'user') ;
  _data_reader text           := quote_ident(_project_schema_prefix || 'reader') ;
  _data_reader_basic text     := quote_ident(_project_schema_prefix || 'reader_basic') ;
  _data_writer text           := quote_ident(_project_schema_prefix || 'writer') ;
  _data_owner text            := quote_ident(_project_schema_prefix || 'owner') ;
BEGIN

  PERFORM zz_utils.setup_create_role(role_name:=_data_user);
  PERFORM zz_utils.setup_create_role(role_name:=_data_reader, inroles:=ARRAY[_data_user]);
  PERFORM zz_utils.setup_create_role(role_name:=_data_reader_basic, inroles:=ARRAY[_data_user]);
  PERFORM zz_utils.setup_create_role(role_name:=_data_writer, inroles:=ARRAY[_data_reader]);
  PERFORM zz_utils.setup_create_role(role_name:=_data_owner, inroles:=ARRAY[_data_writer]);

  -- reader privileges
  EXECUTE('
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _data_owner || ' GRANT SELECT ON SEQUENCES TO ' || _data_reader || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _data_owner || ' GRANT SELECT, REFERENCES ON TABLES TO ' || _data_reader || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _data_owner || ' GRANT SELECT ON SEQUENCES TO ' || _data_reader_basic || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _data_owner || ' GRANT SELECT, REFERENCES ON TABLES TO ' || _data_reader_basic || ' ;
            -- writer privileges
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _data_owner || ' GRANT USAGE ON SEQUENCES TO ' || _data_writer || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _data_owner || ' GRANT EXECUTE ON FUNCTIONS TO ' || _data_writer || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _data_owner || ' GRANT INSERT, DELETE, UPDATE ON TABLES TO ' || _data_writer || ' ;
        ');
  -- project-level roles
  EXECUTE('
            GRANT ' || _data_owner  || ' TO ' || _project_prefix || 'owner;
            GRANT ' || _data_writer || ' TO ' || _project_prefix || 'writer;
            GRANT ' || _data_reader || ' TO ' || _project_prefix || 'reader;
            GRANT ' || _data_reader_basic || ' TO ' || _project_prefix || 'reader_basic;
            GRANT ' || _data_user   || ' TO ' || _project_prefix || 'user;
        ');

  -- BACKWARD COMPATIBILITY
  -- NB: this is done since backend roles still come through old roles
  -- these should be removed once all projects and references have been migrated to new roles
  BEGIN
      EXECUTE('
                GRANT ' || _data_writer || ' TO zalando_data_writer;
                GRANT ' || _data_reader || ' TO zalando_data_reader;
                GRANT ' || _data_user   || ' TO zalando_data_usage;
            ');
  EXCEPTION WHEN OTHERS THEN
      RAISE INFO 'WARNING! ' USING ERRCODE=SQLSTATE, DETAIL=SQLERRM;
  END;
END;
$$
LANGUAGE plpgsql ;


CREATE OR REPLACE FUNCTION zz_utils.create_project_schema_core_api_roles(schema_name text)
RETURNS VOID AS
$$
DECLARE
  _project_schema_prefix text := zz_utils.get_project_schema_prefix(schema_name) ;
  _project_prefix        text := zz_utils.get_project_schema_prefix('') ;
  _api_user text              := quote_ident(_project_schema_prefix || 'user') ;
  _api_executer text          := quote_ident(_project_schema_prefix || 'executer') ;
  _api_owner text             := quote_ident(_project_schema_prefix || 'owner') ;
  --NB: see set_api_schema_for_data_schema for why we don't automatically link api schemas to a data schema
  --_data_writer text  := project_schema_prefix || 'data_writer';
BEGIN

  PERFORM zz_utils.setup_create_role(role_name:=_api_user);
  PERFORM zz_utils.setup_create_role(role_name:=_api_executer, inroles:=ARRAY[_api_user]);
  PERFORM zz_utils.setup_create_role(role_name:=_api_owner, inroles:=ARRAY[_api_executer]);

  EXECUTE('
            -- executer privileges
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _api_owner || ' REVOKE EXECUTE ON FUNCTIONS FROM public;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _api_owner || ' GRANT EXECUTE ON FUNCTIONS TO ' || _api_executer || ' ;
        ');

  -- project-level roles
  EXECUTE('
            GRANT ' || _api_owner    || ' TO ' || _project_prefix || 'owner;
            GRANT ' || _api_executer || ' TO ' || _project_prefix || 'executer;
            GRANT ' || _api_user    || ' TO ' || _project_prefix || 'user;
        ');

  -- BACKWARD COMPATIBILITY
  -- NB: this is done since backend roles still come through old roles
  -- these should be removed once all projects and references have been migrated to new roles
  BEGIN
      EXECUTE('
                GRANT ' || _api_owner    || ' TO zalando_api_owner;
                GRANT ' || _api_executer || ' TO zalando_api_executor;
                GRANT ' || _api_user    || ' TO zalando_api_usage;
            ');
  EXCEPTION WHEN OTHERS THEN
    RAISE INFO 'WARNING! ' USING ERRCODE=SQLSTATE, DETAIL=SQLERRM;
  END;
END;
$$
LANGUAGE plpgsql ;


-- link an api schema to a data schema
-- NB: several api schemas can use the same data schema
CREATE OR REPLACE FUNCTION zz_utils.bind_api_schema_to_data_schemas(api_schema_name text, data_schema_names text[])
RETURNS VOID AS
$$
DECLARE
  _api_project_schema_prefix text     := zz_utils.get_project_schema_prefix(api_schema_name) ;
  _data_project_schemas_prefix text[] := ARRAY(select zz_utils.get_project_schema_prefix(data_schema)
                                                 from unnest(data_schema_names) t(data_schema)) ;

  _api_owner text    := quote_ident(_api_project_schema_prefix || 'owner') ;
  _data_writers text := (select string_agg(quote_ident(data_prefix || 'writer'), ',')
                           from unnest(_data_project_schemas_prefix) t(data_prefix)) ;
BEGIN
    IF data_schema_names is not NULL THEN
        EXECUTE('GRANT ' || _data_writers    || ' TO ' || _api_owner || ';');
    END IF;
END;
$$
LANGUAGE plpgsql ;


CREATE OR REPLACE FUNCTION zz_utils.bind_data_schema_to_api_schemas(data_schema_name text, api_schema_names text[])
RETURNS VOID AS
$$
DECLARE
  _data_project_schema_prefix   text    := zz_utils.get_project_schema_prefix(data_schema_name) ;
  _api_project_schemas_prefix   text[]    := ARRAY(select zz_utils.get_project_schema_prefix(api_schema)
                                                   from unnest(api_schema_names) t(api_schema)) ;

  _data_owner       text    :=  quote_ident(_data_project_schema_prefix || 'owner') ;
  _api_executers    text    :=  (select string_agg(quote_ident(api_prefix || 'executer'), ',')
                                   from unnest(_api_project_schemas_prefix) t(api_prefix)) ;
BEGIN
    IF api_schema_names is not NULL THEN
        EXECUTE('GRANT ' || _api_executers || ' TO ' || _data_owner || ';');
    END IF;
END;
$$
LANGUAGE plpgsql;


-- make one project-schema a parent of another;
CREATE OR REPLACE FUNCTION zz_utils.link_data_project_roles(parent_schema_name text, children_schema_names text[])
RETURNS VOID AS
$$
DECLARE
  _parent_project_schema_prefix text      := zz_utils.get_project_schema_prefix(parent_schema_name) ;
  _children_project_schema_prefix text[]  := ARRAY(select zz_utils.get_project_schema_prefix(child_schema)
                                                     from unnest(children_schema_names) t(child_schema)) ;
  _parent_data_user text   := quote_ident(_parent_project_schema_prefix || 'user') ;
  _parent_data_reader text  := quote_ident(_parent_project_schema_prefix || 'reader') ;
  _parent_data_reader_basic text  := quote_ident(_parent_project_schema_prefix || 'reader_basic') ;
  _parent_data_writer text  := quote_ident(_parent_project_schema_prefix || 'writer') ;
  _parent_data_owner text   := quote_ident(_parent_project_schema_prefix || 'owner') ;

  _children_data_user text   := (select string_agg(quote_ident(child_prefix || 'user'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
  _children_data_reader text  := (select string_agg(quote_ident(child_prefix || 'reader'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
  _children_data_reader_basic text  := (select string_agg(quote_ident(child_prefix || 'reader_basic'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
  _children_data_writer text  := (select string_agg(quote_ident(child_prefix || 'writer'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
  _children_data_owner text   := (select string_agg(quote_ident(child_prefix || 'owner'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
BEGIN

    IF nullif(children_schema_names, '{}'::text[]) is not NULL THEN
        EXECUTE('
                GRANT ' || _children_data_user   || ' TO ' || _parent_data_user || ';
                GRANT ' || _children_data_reader_basic  || ' TO ' || _parent_data_reader_basic || ';
                GRANT ' || _children_data_reader  || ' TO ' || _parent_data_reader || ';
                GRANT ' || _children_data_writer  || ' TO ' || _parent_data_writer || ';
            ');
        -- this is only added here for foreign-key references and other such privileges
        -- added REFERENCES to _child_reader to take care of this
        --EXECUTE('GRANT ' || _children_data_owner   || ' TO ' || _parent_data_owner || ';');
    END IF;

END;
$$
LANGUAGE plpgsql ;


-- make one project-schema a parent of another;
CREATE OR REPLACE FUNCTION zz_utils.link_api_project_roles(parent_schema_name text, children_schema_names text[])
RETURNS VOID AS
$$
DECLARE
  _parent_project_schema_prefix text     := zz_utils.get_project_schema_prefix(parent_schema_name) ;
  _children_project_schema_prefix text[] := ARRAY(select zz_utils.get_project_schema_prefix(child_schema)
                                                    from unnest(children_schema_names) t(child_schema)) ;

  _parent_api_user text    := quote_ident(_parent_project_schema_prefix || 'user') ;
  _parent_api_executer text := quote_ident(_parent_project_schema_prefix || 'executer') ;
  _parent_api_owner text    := quote_ident(_parent_project_schema_prefix || 'owner') ;

  _children_api_user text    := (select string_agg(quote_ident(child_prefix || 'user'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
  _children_api_executer text := (select string_agg(quote_ident(child_prefix || 'executer'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
  _children_api_owner text    := (select string_agg(quote_ident(child_prefix || 'owner'), ',')
                                    from unnest(_children_project_schema_prefix) t(child_prefix)) ;
BEGIN

    IF nullif(children_schema_names, '{}'::text[]) is not NULL THEN
        EXECUTE('
                GRANT ' || _children_api_user    || ' TO ' || _parent_api_user || ';
                GRANT ' || _children_api_executer || ' TO ' || _parent_api_executer || ';
            ');
        --EXECUTE('GRANT ' || _children_api_owner    || ' TO ' || _parent_api_owner || ';');
    END IF;
END;
$$
LANGUAGE plpgsql ;


CREATE OR REPLACE FUNCTION zz_utils.get_project_schema_owner_role(schema_name text)
RETURNS text AS
$$
DECLARE
  _project_schema_prefix text := zz_utils.get_project_schema_prefix(schema_name) ;
  _owner_role            text := quote_ident(_project_schema_prefix || 'owner') ;
BEGIN
    RETURN _owner_role;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION zz_utils.set_project_schema_owner_role(schema_name text)
RETURNS text AS
$$
DECLARE
  _owner_role text := zz_utils.get_project_schema_owner_role(schema_name) ;
BEGIN
    EXECUTE ('SET ROLE ' || _owner_role || ' ;') ;
    RETURN _owner_role;
END;
$$ LANGUAGE plpgsql;


-- create data and api schemas
-- NB: @schema_name is intentionally extended outside so that DeployCTL can rename it appropriately e.g. for the release APIs
-- NB: @schema_name is not modified at all e.g. with _project_schema_prefix. remember that access-control is done via only the roles
CREATE OR REPLACE FUNCTION zz_utils.create_project_schema(schema_name text, schema_type text, deprecated_schema_owner text
                                                        , skipCreation boolean default false, isPublic boolean default false
                                                        , make_backward_compatible boolean default true)
RETURNS VOID AS
$$
DECLARE
  _project_schema_prefix text := zz_utils.get_project_schema_prefix(schema_name) ;
  _project_prefix        text := zz_utils.get_project_schema_prefix('') ;
  _project_owner         text := _project_prefix || 'owner';
  _user_role            text := quote_ident(_project_schema_prefix || 'user') ;
  _owner_role            text := quote_ident(_project_schema_prefix || 'owner') ;
  _schema_name           text := quote_ident(schema_name) ;

  _data_reader           text := quote_ident(_project_schema_prefix || 'reader') ;
  _data_reader_basic     text := quote_ident(_project_schema_prefix || 'reader_basic') ;
  _data_writer           text := quote_ident(_project_schema_prefix || 'writer') ;
  _api_executer          text := quote_ident(_project_schema_prefix || 'executer') ;
  _deprecated_schema_owner text := quote_ident(deprecated_schema_owner);
  _abstract_owners       text := ('zalando_owner' || case when schema_name NOT IN ('zz_commons', 'zcpe_data', 'pgq') then ',' || _project_owner else '' end
                                    || case when make_backward_compatible then ',' || _deprecated_schema_owner else '' end );
BEGIN

  IF not skipCreation --useful for patching only
  THEN
    EXECUTE ('CREATE SCHEMA ' || _schema_name || ' AUTHORIZATION ' || _owner_role || ' ;') ;
  ELSE
     EXECUTE('ALTER SCHEMA ' || _schema_name || ' OWNER TO ' || _owner_role);
  END IF;

  EXECUTE ('GRANT USAGE ON SCHEMA ' || _schema_name || ' TO ' || _user_role || ';') ;
  -- NB: BACKWARD COMPATIBILITY: some schemas allow access to PUBLIC
  IF isPublic THEN
    EXECUTE ('GRANT USAGE ON SCHEMA ' || _schema_name || ' TO PUBLIC ;') ;
  END IF;

  -- DB-DIFFS have to be done by schema_owner role; however it may not be so convenient to set it multiple times for the different schemas
  -- it could be done with the project_owner role; all schemas in the project are then accessible; however ownership is not transfered to schema_owner
  -- _deprecated_schema_owner => BACKWARD-COMPATIBILITY: older roles added for backward compatibility i.e. until DB-DIFFS and other sources set roles appropriately
  IF lower(schema_type) = 'data'
  THEN
    -- owner privileges
    EXECUTE('
            -- normally we should be able to redirect ownership but this is not yet a feature of PostgreSQL
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT ALL ON SEQUENCES TO ' || _owner_role || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT ALL ON TABLES TO ' || _owner_role || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT ALL ON FUNCTIONS TO ' || _owner_role || ' ;

            -- reader privileges
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT SELECT ON SEQUENCES TO ' || _data_reader || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT SELECT, REFERENCES ON TABLES TO ' || _data_reader || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT SELECT ON SEQUENCES TO ' || _data_reader_basic || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT SELECT, REFERENCES ON TABLES TO ' || _data_reader_basic || ' ;
            -- writer privileges
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT USAGE ON SEQUENCES TO ' || _data_writer || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT EXECUTE ON FUNCTIONS TO ' || _data_writer || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT INSERT, DELETE, UPDATE ON TABLES TO ' || _data_writer || ' ;
        ');
  ELSIF lower(schema_type) = 'api'
  THEN
    EXECUTE('
            -- normally we should be able to redirect ownership but this is not yet a feature of PostgreSQL
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT ALL ON FUNCTIONS TO ' || _owner_role || ' ;
            ALTER DEFAULT PRIVILEGES FOR ROLE ' || _abstract_owners || ' IN SCHEMA ' || _schema_name || ' GRANT EXECUTE ON FUNCTIONS TO ' || _api_executer || ' ;
        ');
  END IF;
END;
$$
LANGUAGE plpgsql ;


--NB: append_searchpath=FALSE means SET search_path anew i.e. don't append to existing search_path. NULL means don't set search_path at all
DROP FUNCTION IF EXISTS zz_utils.create_project_schema_data_env(text, text[], boolean, text, boolean, boolean);
CREATE OR REPLACE FUNCTION zz_utils.create_project_schema_data_env(
                                schema_name text, children_schema_names text[] default null::text[]
                                , api_schema_names text[] default null::text[], append_searchpath boolean default NULL
                                , deprecated_schema_owner text default 'zalando', isPublic boolean default false
                                , skipCreation boolean default false, make_backward_compatible boolean default true)
RETURNS VOID AS
$$
BEGIN
    -- 1. switch to invoker; usually superuser
    RESET ROLE;
    -- 2. create the roles specific for this project and schema
    PERFORM zz_utils.create_project_schema_core_data_roles(schema_name:=schema_name);
    -- 3. create the schema
    PERFORM zz_utils.create_project_schema(schema_name:=schema_name, schema_type:='data', deprecated_schema_owner:=deprecated_schema_owner
                                         , isPublic:=isPublic, skipCreation:=skipCreation, make_backward_compatible:=make_backward_compatible);
    -- 4.A sometimes schema should have access to other child-schemas
    PERFORM zz_utils.link_data_project_roles(parent_schema_name:=schema_name, children_schema_names:=children_schema_names);
    -- 4.B in very few cases data-roles access api-roles e.g. PGQ
    PERFORM zz_utils.bind_data_schema_to_api_schemas(data_schema_name:=schema_name, api_schema_names:=api_schema_names);
    -- 5. set the search_path; note that some <zalos> data-objects are not schema-qualified
    IF append_searchpath = TRUE THEN  --this is normally for zalos modules
        EXECUTE 'SET search_path to ' || schema_name ||', ' || current_setting('search_path') || ';';
    ELSIF append_searchpath = FALSE THEN
        EXECUTE 'SET search_path to ' || schema_name ||', public;';
    END IF;
    -- 6. set the default search path for the database
    --EXECUTE 'ALTER DATABASE ' || CURRENT_DATABASE() || ' SET search_path to ' || current_setting('search_path') || ';';
    -- 7. set the role to be the owner of the coming objects; this is why it not necessary for object files to do this
    PERFORM zz_utils.set_project_schema_owner_role(schema_name:=schema_name);
END;
$$
LANGUAGE plpgsql ;


--NB: append_searchpath=FALSE means SET search_path anew i.e. don't append to existing search_path. NULL means don't set search_path at all
CREATE OR REPLACE FUNCTION zz_utils.create_project_schema_api_env(
                                schema_name text, data_schema_names text[], api_schema_names text[] default null::text[]
                                , append_searchpath boolean default false, deprecated_schema_owner text default 'zalando_api_owner'
                                , make_backward_compatible boolean default true)
RETURNS VOID AS
$$
BEGIN
    -- 1. switch to invoker; usually superuser
    RESET ROLE;
    -- 2. create the roles specific for this project and schema
    PERFORM zz_utils.create_project_schema_core_api_roles(schema_name:=schema_name);
    -- 3. create the schema
    PERFORM zz_utils.create_project_schema(schema_name:=schema_name, schema_type:='api', deprecated_schema_owner:=deprecated_schema_owner
                                         , make_backward_compatible:=make_backward_compatible) ;
    -- 4.A sometimes schema should have access to other child-schemas
    PERFORM zz_utils.link_api_project_roles(parent_schema_name:=schema_name, children_schema_names:=api_schema_names);
    -- 4.B bind api to the data schemas that it should access
    PERFORM zz_utils.bind_api_schema_to_data_schemas(api_schema_name:=schema_name, data_schema_names:=data_schema_names);
    -- 5. set the search_path; note that api objects are not schema-qualified
    IF append_searchpath = TRUE THEN  --this is normally for zalos modules
        EXECUTE 'SET search_path to ' || schema_name ||', ' || current_setting('search_path') || ';';
    ELSIF append_searchpath = FALSE THEN
        EXECUTE 'SET search_path to ' || schema_name ||', public;';
    END IF;
    -- 6. set the default search path for the database
    EXECUTE 'ALTER DATABASE ' || CURRENT_DATABASE() || ' SET search_path to ' || current_setting('search_path') || ';';
    -- 7. set the role to be the owner of the coming objects; this is why it not necessary for object files to do this
    PERFORM zz_utils.set_project_schema_owner_role(schema_name:=schema_name);

END;
$$
LANGUAGE plpgsql ;
