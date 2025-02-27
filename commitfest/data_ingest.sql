BEGIN;

DROP TABLE IF EXISTS thread_summaries cascade;

CREATE TABLE thread_summaries (
    id TEXT PRIMARY KEY,
    summary TEXT,
    status TEXT,
    activity TEXT,
    complexity INTEGER,
    problem TEXT,
    would_benefit_from_new_reviewer TEXT
);

\copy thread_summaries FROM 'thread_summaries.csv' DELIMITER ',' CSV HEADER QUOTE '"' ESCAPE '\';

DROP TABLE IF EXISTS attachment_stats cascade;

CREATE TABLE attachment_stats (

    ID TEXT PRIMARY KEY,
    file TEXT,
    additions INTEGER,
    deletion INTEGER,
    link TEXT,
    message_id TEXT
);

\copy attachment_stats FROM 'attachment_stats.csv' DELIMITER ',' CSV HEADER QUOTE '"' ESCAPE '\';


DROP TABLE IF EXISTS patch_message cascade;

CREATE TABLE patch_message (
    PATCH TEXT,
    MESSAGE TEXT
);


\copy patch_message FROM 'message_patch.csv' DELIMITER ',' CSV HEADER QUOTE '"' ESCAPE '\';

DROP TABLE IF EXISTS patches cascade;

CREATE TABLE patches (
    id TEXT,
    patch_id TEXT PRIMARY KEY,
    message_ids TEXT,
    name text
);


\copy patches FROM 'patches.csv' DELIMITER ',' CSV HEADER;


DROP TABLE IF EXISTS thread_stats cascade;

CREATE TABLE thread_stats (
    message_id text primary key,
    last_activity timestamp,
    author text,
    reviewer_list json
);


\copy thread_stats FROM 'thread_stats.csv' DELIMITER ',' CSV HEADER;

DROP TABLE IF EXISTS predicted_committer cascade;

CREATE TABLE predicted_committer (
    thread text primary key,
    a text,
    score_a float,
    terms_a text,
    b text,
    score_b float,
    terms_b text,
    c text,
    score_c float,
    terms_c text
);


\copy predicted_committer FROM 'predicted_committers.csv' DELIMITER ',' CSV HEADER;

DROP TABLE IF EXISTS contributor_names cascade;

CREATE TABLE contributor_names (
    name text primary key
);


\copy contributor_names FROM 'contributor_names.csv' DELIMITER ',' CSV HEADER;

create or replace view contributors as 
    SELECT name display_name, normalize_name_email(name) name
    from contributor_names
;

COMMIT;
