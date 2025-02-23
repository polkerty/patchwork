BEGIN;

DROP TABLE IF EXISTS thread_summaries;

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

DROP TABLE IF EXISTS attachment_stats;

CREATE TABLE attachment_stats (

    ID TEXT PRIMARY KEY,
    file TEXT,
    additions INTEGER,
    deletion INTEGER,
    link TEXT,
    message_id TEXT
);

\copy attachment_stats FROM 'attachment_stats.csv' DELIMITER ',' CSV HEADER QUOTE '"' ESCAPE '\';


DROP TABLE IF EXISTS patch_message;

CREATE TABLE patch_message (
    PATCH TEXT,
    MESSAGE TEXT PRIMARY KEY
);


\copy patch_message FROM 'message_patch.csv' DELIMITER ',' CSV HEADER QUOTE '"' ESCAPE '\';


COMMIT;
