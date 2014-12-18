CREATE OR REPLACE FUNCTION zz_commons.get_next_unique_id ( virtual_shard_id bigint, seq regclass ) RETURNS bigint AS
$$
  SELECT ( (floor(extract(epoch from clock_timestamp()) * 1000)::bigint - 1325372400000) << 23 )::bigint -- to start our ID, we fill the left-most 41 bits with this value with a left-shift
            | ( $1 << 10)
            | ( nextval($2) & x'3FF'::bigint /* last 10 bits */ )::bigint
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION zz_commons.decode_unique_id ( id INOUT bigint, OUT creation_date timestamp, OUT virtual_shard_id bigint, OUT sequence_number bigint , OUT ms_since_start bigint, OUT time_left interval ) RETURNS record AS
$$
  SELECT $1,
         (( $1 >> 23 )) * '1 ms'::interval + '2012-01-01 00:00:00'::timestamp,
         ($1 & ((1<<23)-1)::bigint)>>10, /* 23-11 */
         $1 & ((1<<10)-1)::bigint,
         (( $1 >> 23 )),
         justify_interval (( ( ( 1::bigint << 41 ) - 1) - ( $1 >> 23 )) * '1 ms'::interval) /* 10-1 */
$$ LANGUAGE sql;
