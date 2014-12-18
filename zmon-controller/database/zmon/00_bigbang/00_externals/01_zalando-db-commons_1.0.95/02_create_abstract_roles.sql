--cluster-level                  project level
--owner------------------------> owner
--+---writer-------------------> writer
--|   +---reader(_basic)-------> reader(basic)
--|       +---user-------------> user
--+---executer-----------------> executer
--    +---user-----------------> user
--+---
reset role;
DO
$$
DECLARE
    -- cluster-level roles
    _zalando                text := 'zalando';
    _zalandos               text := 'zalandos';     -- A flag for human users
    _zalando_user_sink      text := 'zalando_user_sink';    --garbage object collector from to-be-deleted roles
    _zalando_prefix         text := 'zalando_';
    _zalando_owner          text := _zalando_prefix || 'owner';
    _zalando_executer       text := _zalando_prefix || 'executer';
    _zalando_writer         text := _zalando_prefix || 'writer';
    _zalando_reader         text := _zalando_prefix || 'reader';
    _zalando_reader_basic   text := _zalando_prefix || 'reader_basic';
    _zalando_user           text := _zalando_prefix || 'user';
    -- project-level roles
    _project_prefix         text := (SELECT zz_utils.get_project_schema_prefix('')) ;
    _project_owner          text := _project_prefix || 'owner';
    _project_executer       text := _project_prefix || 'executer';
    _project_writer         text := _project_prefix || 'writer';
    _project_reader         text := _project_prefix || 'reader';
    _project_reader_basic   text := _project_prefix || 'reader_basic';
    _project_user           text := _project_prefix || 'user';
BEGIN
    -- the legendary zalando role
    -- in the future we may have to grant superuser to zalando so that ownership of created objects is appropriately transfered to schema_owners
    PERFORM zz_utils.setup_create_role(role_name:=_zalando);
    PERFORM zz_utils.setup_create_role(role_name:=_zalandos);
    PERFORM zz_utils.setup_create_role(role_name:=_zalando_user_sink);

    -- NB: No ownership of schema objects should be made to abstract roles
    -- the chaining within the level is disabled i.e. NO grant zalando_user to zalando_reader
    -- this way we don't have too many memberships

    -- project-level roles
    PERFORM zz_utils.setup_create_role(role_name:=_project_user);
    PERFORM zz_utils.setup_create_role(role_name:=_project_reader_basic/*, inroles:=ARRAY[_project_user]*/);
    PERFORM zz_utils.setup_create_role(role_name:=_project_reader/*, inroles:=ARRAY[_project_user]*/);
    PERFORM zz_utils.setup_create_role(role_name:=_project_writer/*, inroles:=ARRAY[_project_reader]*/);
    PERFORM zz_utils.setup_create_role(role_name:=_project_executer/*, inroles:=ARRAY[_project_user]*/);
    PERFORM zz_utils.setup_create_role(role_name:=_project_owner/*, inroles:=ARRAY[_project_writer, _project_executer]*/);
    -- cluster-level roles
    PERFORM zz_utils.setup_create_role(role_name:=_zalando_user, inroles:=ARRAY[_project_user]);
    PERFORM zz_utils.setup_create_role(role_name:=_zalando_reader_basic, inroles:=ARRAY[_project_reader_basic/*, _zalando_user*/]);
    PERFORM zz_utils.setup_create_role(role_name:=_zalando_reader, inroles:=ARRAY[_project_reader/*, _zalando_user*/]);
    PERFORM zz_utils.setup_create_role(role_name:=_zalando_writer, inroles:=ARRAY[_project_writer/*, _zalando_reader*/]);
    PERFORM zz_utils.setup_create_role(role_name:=_zalando_executer, inroles:=ARRAY[_project_executer/*, _zalando_user*/]);
    PERFORM zz_utils.setup_create_role(role_name:=_zalando_owner, inroles:=ARRAY[_project_owner/*, _zalando_writer, _zalando_executer*/]);

    EXECUTE('
        ALTER DEFAULT PRIVILEGES FOR ROLE ' || _zalando_owner || ',' || _project_owner || ' REVOKE EXECUTE ON FUNCTIONS FROM public;
        ');

    -- would NOT be required if we make zalando superuser
    EXECUTE ('GRANT '|| _zalando_owner ||' TO zalando;');
    -- backward compatibility
    BEGIN
        ALTER DEFAULT PRIVILEGES FOR ROLE zalando_api_owner REVOKE EXECUTE ON FUNCTIONS FROM public;
    EXCEPTION WHEN OTHERS THEN
        RAISE INFO 'WARNING! ' USING ERRCODE=SQLSTATE, DETAIL=SQLERRM;
    END;
END;
$$;

