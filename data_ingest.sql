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

TRUNCATE TABLE thread_summaries;

\copy thread_summaries FROM 'thread_summaries.csv' DELIMITER ',' CSV HEADER QUOTE '"' ESCAPE '\';
