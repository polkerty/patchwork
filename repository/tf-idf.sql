begin;

-- TF
drop materialized view if exists contrib_tf cascade;

create  materialized view contrib_tf as 
    select 
        normalize_name_email(author) author,
         file, 
         sum(ln(1 + additions + deletions)) tf 
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
    select 
        p.patch patch,
        tf.file file, 
        tf.author reviewer, 
        a.additions,
        a.deletion,
        tf.tf * idf.idf unweighted_tf_idf,
        ln(1 + a.additions + a.deletion) * tf.tf * idf.idf tf_idf
    from 
        contrib_tf tf
        join contrib_idf idf on tf.file = idf.file
        join attachment_stats a on a.file = tf.file
        join patch_message p on p.message = a.message_id
;

drop materialized view if exists contrib_tf_idf cascade;

create materialized view contrib_tf_idf as 
    select reviewer, patch, sum(tf_idf)
    from
        perfile_tf_idf f
    group by 1, 2
    order by 1 asc, 2 desc;
;

commit;