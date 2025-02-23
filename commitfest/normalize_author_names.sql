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
    -- 2) Remove trailing email address in angle brackets.
    --    e.g. "Foo Bar <foo@example.org>" -> "Foo Bar"
    ----------------------------------------------------------------------
    step := REGEXP_REPLACE(step, '<[^>]+>', '');

    ----------------------------------------------------------------------
    -- 3) Convert accented characters to unaccented forms
    --    (e.g. "Á" -> "A"). Requires the "unaccent" extension.
    ----------------------------------------------------------------------
    step := unaccent(step);

    ----------------------------------------------------------------------
    -- 4) Normalize spacing: collapse multiple spaces to one, and trim.
    ----------------------------------------------------------------------
    step := REGEXP_REPLACE(step, '\s+', ' ', 'g');
    step := btrim(step);

    ----------------------------------------------------------------------
    -- 5) If there's exactly one comma, assume "Lastname, First..."
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
    -- 6) Remove single-letter words (typically middle initials),
    --    and initcap() each word.
    ----------------------------------------------------------------------
    WITH parts AS (
        SELECT regexp_split_to_array(step, '\s+') AS arr
    )
    SELECT string_agg(
             CASE
               -- Remove single-letter words (e.g. "O" or "O.")
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

    -- Final space cleanup
    step := REGEXP_REPLACE(step, '\s+', ' ', 'g');
    step := btrim(step);

    RETURN step;  -- Name only, no email
END;
$$;
