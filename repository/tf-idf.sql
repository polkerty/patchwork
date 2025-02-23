drop materialized view if exists contrib_tf;

create  materialized view contrib_tf as 
    select 
        normalize_name_email(author) contrib_name,
         file, 
         sum(log(1 + additions + deletions)) tf 
    from commitstats 
    group by 1, 2;