begin;

drop materialized view if exists contrib_tf;

create  materialized view contrib_tf as 
    select 
        normalize_name_email(author) author,
         file, 
         sum(log(1 + additions + deletions)) tf 
    from commitstats 
    group by 1, 2;


drop materialized view if exists contrib_idf;

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

commit;