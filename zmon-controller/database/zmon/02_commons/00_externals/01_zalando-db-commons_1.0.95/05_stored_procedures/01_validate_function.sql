--http://techblog.zalando.net/2013/06/plpgsql_lint-2/

  create or replace function zz_commons.validate_function(function_signature regprocedure)
  returns void as
  $function$
    begin

      if current_database() like 'local_%'
      then
        EXECUTE  ('ALTER FUNCTION ' || function_signature::text ||
                                  ' SET plpgsql.enable_lint to true;') ;
        --excute the function with NULL arguments
        EXECUTE ('SELECT ' ||
                case when trim(regexp_replace(function_signature::text, E'(^[^\\(]*\\(|\\).*)', '', 'g')) <> ''
                     then replace(replace(function_signature::text,',',',NULL::'),'(','(NULL::')
                     else function_signature::text  end || ' ;');

        raise exception SQLSTATE 'P0999';

      end if;
    --catch the exception we raised so that there would be no exception raised
    --but there would be a rollback of the functions tasks
    exception when SQLSTATE 'P0999' then
        EXECUTE  ('ALTER FUNCTION ' || function_signature::text ||
                                  ' SET plpgsql.enable_lint to false;') ;
    end;
  $function$ language plpgsql;
