-- DROP FUNCTION get_substrings(text, int)
CREATE OR REPLACE FUNCTION get_substrings(t text, length int default 2)
RETURNS text[]
IMMUTABLE STRICT LANGUAGE SQL
AS $SQL$

/* --test

 drop table substing_search_test_table ;
 create table substing_search_test_table as select substr(  md5(s.i::text || '_test_text'), 1, 7 ) as tmd from generate_series( 1, 1000000 ) as s(i);

 SET maintenance_work_mem TO '128MB';
 SET work_mem TO '128MB';
 SET search_path TO zz_utils, public;


 create index substing_search_test_table_gin2_idx on substing_search_test_table using gin ( (get_substrings(tmd, 2)) );
 create index substing_search_test_table_gin3_idx on substing_search_test_table using gin ( (get_substrings(tmd, 3)) );
 create index substing_search_test_table_gin4_idx on substing_search_test_table using gin ( (get_substrings(tmd, 4)) );

 select tmd, get_substrings(tmd) from substing_search_test_table limit 50;

 -- a sequential scan using like (~250 - ~600 ms)
 select tmd from substing_search_test_table where tmd like '%1d54c%';
 -- an index scan over GIN index (~20 - ~40 ms)
 select tmd from substing_search_test_table where ARRAY[ '1d54c' ] <@ get_substrings(tmd);

 -- more tests with different minimal substing parameter using different indexes
 select tmd from substing_search_test_table where tmd like '%1d54%'; -- ~250 ms
 select tmd from substing_search_test_table where ARRAY[ '1d54'  ] <@ get_substrings(tmd, 2); -- ~40 ms
 select tmd from substing_search_test_table where ARRAY[ '1d54'  ] <@ get_substrings(tmd, 4); -- ~35 ms

 select tmd from substing_search_test_table where tmd like '%d54%'; -- ~250 ms
 select tmd from substing_search_test_table where ARRAY[ 'd54'   ] <@ get_substrings(tmd, 2); -- ~80 ms
 select tmd from substing_search_test_table where ARRAY[ 'd54'   ] <@ get_substrings(tmd, 4); -- ~40 ms

 -- more tests with bigger result set (23450 rows)
 select tmd from substing_search_test_table where ARRAY[ 'd5' ] <@ get_substrings(tmd); -- ~250 - ~600 ms
 select tmd from substing_search_test_table where tmd like '%d5%'; -- ~270 ms - ~560 ms

 select ARRAY[ 'alent' ] && get_substrings('Valentine', 4 )

 select get_substrings('Valentine', 5 )
 select get_substrings('Valentine', 4 )
 select get_substrings('Valentine', 3 )
 select get_substrings('Valentine', 2 )
 select get_substrings('Valentine', 1 )

 select get_substrings('123', 1 )
 select get_substrings('123', 2 )
 select get_substrings('123', 3 )
 select get_substrings('123', 4 )


 */

select coalesce( array_agg( substr( $1, i, length( $1 ) - e + 1 ) ), ARRAY[ $1 ] )
  from (
        select w.i,
               generate_series( w.i, length( $1 ) - $2 + 1 ) as e
          from generate_series( 1, length( $1 ) - $2 + 1 ) as w(i)
       ) as s
$SQL$;