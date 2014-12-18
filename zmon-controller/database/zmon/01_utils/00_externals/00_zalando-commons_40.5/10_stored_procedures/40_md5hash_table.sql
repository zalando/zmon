CREATE OR REPLACE FUNCTION zz_utils.md5hash_table(p_table regclass, OUT total INTEGER, OUT hash TEXT) RETURNS RECORD
AS $sql$
DECLARE
    sql_stmt TEXT;
    p_key_columns TEXT;
BEGIN
    -- fetch primary key columns. We need to order results
    -- by it to have a predictable order of rows supplied for hashing.
    SELECT string_agg(attname, ',' ORDER BY attname) INTO p_key_columns
    FROM pg_catalog.pg_attribute a
    WHERE  attrelid = p_table::oid AND attnum > 0 AND attisdropped = 'f'
    AND attnum = ANY((SELECT indkey FROM pg_index WHERE indrelid = a.attrelid AND indisprimary)::int[]);

    IF p_key_columns IS NULL
    THEN
        RAISE EXCEPTION 'Cannot find primary key for table %', p_table::text;
    END IF;

    SELECT E'SELECT count(*) as total, md5(string_agg(t.*::text, \',\' ORDER BY '||p_key_columns||')) as hash FROM (SELECT '||string_agg(quote_ident(attname),',' ORDER BY attname)||' FROM '||p_table::TEXT||') t;'
    INTO sql_stmt
    FROM pg_attribute
    WHERE attrelid = p_table::oid
    AND attisdropped is false and attnum > 0
    AND attname NOT LIKE '%modified%'
    AND attname NOT LIKE '%created%';
    IF sql_stmt IS NOT NULL
    THEN
        EXECUTE sql_stmt INTO total, hash;
    ELSE
        total := 0;
        hash = NULL;
    END IF;
END;
$sql$
LANGUAGE plpgsql STABLE;

