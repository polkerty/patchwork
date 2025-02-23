begin;

-- TF
drop materialized view if exists contrib_tf cascade;

create  materialized view contrib_tf as 
    select 
        normalize_name_email(author) author,
         file, 
         sum(log(1 + additions + deletions)) tf 
    from commitstats 
    group by 1, 2;

-- IDF
drop materialized view if exists contrib_idf cascade;

create materialized view contrib_idf as 
    with file_cnt as (
        select file, count(*) cnt
        from contrib_tf
        group by 1
    )
    select 
        file,
        (select count(distinct author) from contrib_tf) / cnt idf
    from file_cnt;


-- TF-IDF!
drop materialized view if exists per_file_tf_idf cascade;

create materialized view perfile_tf_idf as
    select a.message_id message_id, tf.file file, tf.author reviewer, tf.tf * idf.idf tf_idf
    from 
        contrib_tf tf
        left join contrib_idf idf on tf.file = idf.file
        left join attachment_stats a on a.file = tf.file
;

drop materialized view if exists contrib_tf_idf cascade;

create materialized view contrib_tf_idf as 
    select reviewer, p.patch, sum(tf_idf)
    from
        perfile_tf_idf f
        left join patch_message p on p.message = f.message_id
    group by 1, 2
    order by 1 asc, 2 desc;
;

commit;