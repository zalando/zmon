CREATE OR REPLACE FUNCTION zz_utils.change_project_schema_owner(schema_name text, new_owner text)
RETURNS setof text AS
$$
DECLARE
    obj text;
    objid int;
BEGIN

    -- ensure permission to reference objects while ownership is being switched in several transactions
    RETURN NEXT 'ALTER ROLE ' || new_owner || ' WITH SUPERUSER;';

    -- the classical way of doing this is with pg_dump and replace ownership lines

    -- change TYPE ownership

    FOR obj IN  SELECT typname
                  FROM pg_type typ
                  JOIN pg_namespace nsp ON typ.typnamespace = nsp.oid
                 WHERE nspname = schema_name
                   AND (typ.typrelid = 0 or (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = typ.typrelid))
                   AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = typ.typelem AND el.typarray = typ.oid)
    LOOP
        BEGIN
            RETURN NEXT 'ALTER TYPE ' || schema_name || '.' || obj || ' OWNER TO ' || new_owner || ';';
            --Type Grantors are not updated by ownership change
            RETURN NEXT 'GRANT USAGE ON TYPE ' || schema_name || '.' || obj || ' TO PUBLIC;';
        EXCEPTION WHEN OTHERS THEN
            RAISE INFO 'The TYPE % could not be dealt with: ', obj USING ERRCODE = SQLSTATE, DETAIL = SQLERRM;
        END;
    END LOOP;

    -- change SEQUENCE ownership

    FOR obj IN  SELECT *
                  FROM pg_class rel
                  JOIN pg_namespace nsp ON rel.relnamespace = nsp.oid
                 WHERE rel.relkind = 'S' and nsp.nspname = schema_name
    LOOP
        BEGIN
            RETURN NEXT 'ALTER SEQUENCE ' || schema_name || '.' || obj || ' OWNER TO ' || new_owner || ';';
        EXCEPTION WHEN OTHERS THEN
            RAISE INFO 'The SEQUENCE % could not be dealt with: ', obj USING ERRCODE = SQLSTATE, DETAIL = SQLERRM;
        END;
    END LOOP;

    -- change TABLE ownership

    FOR obj IN  SELECT relname
                  FROM pg_class rel
                  JOIN pg_namespace nsp ON rel.relnamespace = nsp.oid
                 WHERE rel.relkind = 'r' and nsp.nspname = schema_name
    LOOP
        BEGIN
            RETURN NEXT 'ALTER TABLE ' || schema_name || '.' || obj || ' OWNER TO ' || new_owner || ';';
        EXCEPTION WHEN OTHERS THEN
            RAISE INFO 'The TABLE % could not be dealt with: ', obj USING ERRCODE = SQLSTATE, DETAIL = SQLERRM;
        END;
    END LOOP;

    -- change VIEW ownership

    FOR obj IN  SELECT relname
                  FROM pg_class rel
                  JOIN pg_namespace nsp ON rel.relnamespace = nsp.oid
                 WHERE rel.relkind in ('v','m') and nsp.nspname = schema_name
    LOOP
        BEGIN
            RETURN NEXT 'ALTER VIEW ' || schema_name || '.' || obj || ' OWNER TO ' || new_owner || ';';
        EXCEPTION WHEN OTHERS THEN
            RAISE INFO 'The VIEW % could not be dealt with: ', obj USING ERRCODE = SQLSTATE, DETAIL = SQLERRM;
        END;
    END LOOP;

    -- change FUNCTION ownership

    FOR objid IN SELECT proc.oid
                  FROM pg_proc proc
                  JOIN pg_namespace nsp ON proc.pronamespace = nsp.oid
                 WHERE nsp.nspname = schema_name
    LOOP
        BEGIN
            RETURN NEXT 'ALTER FUNCTION ' || objid::oid::regproc || '(' ||
                        regexp_replace( pg_get_function_arguments(objid::oid),  E' default [^,)]+([,)])?', E' \\1', 'ig') ||
                            ') OWNER TO ' || new_owner || ';';
        EXCEPTION WHEN OTHERS THEN
            RAISE INFO 'The FUNCTION % could not be dealt with: ', objid::oid::regproc USING ERRCODE = SQLSTATE, DETAIL = SQLERRM;
        END;
    END LOOP;

    RETURN NEXT 'ALTER SCHEMA ' || schema_name || ' OWNER TO ' || new_owner || ';';

    RETURN NEXT 'ALTER ROLE ' || new_owner || ' WITH NOSUPERUSER;';

    RETURN;

END;
$$
language plpgsql;
