-- 1. Drop table if it already exists
DROP TABLE IF EXISTS commitstats;

-- 2. Create the new table
CREATE TABLE commitstats (
    author TEXT,
    file TEXT,
    additions INT,
    deletions INT,
    commit TEXT,
    date TIMESTAMPTZ,
    assoc_type TEXT
);

-- 3. (Optional) Truncate if we want to be sure we're starting from an empty table
TRUNCATE TABLE commitstats;

-- 4. Ingest data from the JSON file using jq to transform JSON -> CSV
\copy commitstats (author, file, additions, deletions, commit, date, assoc_type) FROM PROGRAM 'jq -r ".[] | @csv" repo_history.json' CSV QUOTE '"' ESCAPE '\';