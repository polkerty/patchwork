CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE OR REPLACE FUNCTION normalize_name_email(in_name text)
RETURNS text LANGUAGE plpgsql AS
$$
DECLARE
    raw_name    text := in_name;
    step        text;
    splittedArr text[];
BEGIN
    ----------------------------------------------------------------------
    -- 1) Strip out "Author: " if present (case-insensitive).
    ----------------------------------------------------------------------
    step := REGEXP_REPLACE(raw_name, 'Author:', '', 'i');

    ----------------------------------------------------------------------
    -- 2) Remove any angle-bracketed text, e.g. emails. 
    ----------------------------------------------------------------------
    step := REGEXP_REPLACE(step, '<[^>]+>', '', 'g');

    ----------------------------------------------------------------------
    -- 3) Remove any parenthetical remarks, e.g. "(Pn Japan Fsip)" 
    ----------------------------------------------------------------------
    step := REGEXP_REPLACE(step, '\(.*?\)', ' ', 'g');

    ----------------------------------------------------------------------
    -- 4) Convert accented characters to unaccented forms 
    --    (Requires "unaccent" extension).
    ----------------------------------------------------------------------
    step := unaccent(step);

    ----------------------------------------------------------------------
    -- 5) Normalize spacing: collapse multiple spaces to one, and trim.
    ----------------------------------------------------------------------
    step := REGEXP_REPLACE(step, '\s+', ' ', 'g');
    step := btrim(step);

    ----------------------------------------------------------------------
    -- 6) If there's exactly one comma, assume "Lastname, First..."
    --    Then reorder to "First ... Last".
    ----------------------------------------------------------------------
    IF step ~ '^[^,]+,[^,]+$' THEN
        SELECT regexp_split_to_array(step, '\s*,\s*') INTO splittedArr;
        IF array_length(splittedArr, 1) = 2 THEN
            step := splittedArr[2] || ' ' || splittedArr[1];
            step := REGEXP_REPLACE(step, '\s+', ' ', 'g');
            step := btrim(step);
        END IF;
    END IF;

    ----------------------------------------------------------------------
    -- 7) Remove single-letter words, e.g. middle initials "O." 
    --    and initcap() each word.
    ----------------------------------------------------------------------
    WITH parts AS (
        SELECT regexp_split_to_array(step, '\s+') AS arr
    )
    SELECT string_agg(
             CASE
               WHEN length(regexp_replace(word, '\W', '', 'g')) = 1 THEN ''
               ELSE initcap(word)
             END,
             ' '
           )
      INTO step
      FROM (
         SELECT unnest(arr) AS word
         FROM parts
      ) t
      WHERE word <> '';

    ----------------------------------------------------------------------
    -- 8) Final space cleanup
    ----------------------------------------------------------------------
    step := REGEXP_REPLACE(step, '\s+', ' ', 'g');
    step := btrim(step);

    RETURN step;
END;
$$;
