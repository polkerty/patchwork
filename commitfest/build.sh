python analyze_commitfest.py        # scrape commitfest site, postgres mailing list, and perform LLM analysis. Output data as CSVs
psql -p 6565 -f data_ingest.sql     # upload CSVs to local postgres
psql -p 6565 -f ../repository/tf-idf.sql      # analyze postgres repo for usage and build patch recommendations


# Dumping JSON out for frontend


# thread_summaries: LLM analysis of mailing threads
psql -p 6565 -c "\
  SELECT json_agg(row_to_json(t)) \
  FROM (SELECT * FROM thread_summaries) t;" \
  -t -A > ../frontend/data/thread_summaries.json

# contrib_idf: Relevance rank of patches per contributor
psql -p 6565 -c "\
  SELECT json_agg(row_to_json(t)) \
  FROM (SELECT * FROM contrib_idf) t;" \
  -t -A > ../frontend/data/contrib_idf.json

# patches: Commitfest data about patches
psql -p 6565 -c "\
  SELECT json_agg(row_to_json(t)) \
  FROM (SELECT * FROM patches) t;" \
  -t -A > ../frontend/data/patches.json

# thread_stats: more info about threads
psql -p 6565 -c "\
  SELECT json_agg(row_to_json(t)) \
  FROM (SELECT * FROM thread_stats) t;" \
  -t -A > ../frontend/data/thread_stats.json

# patch_message: link a patch to its mailing threads, and vice versa
psql -p 6565 -c "\
  SELECT json_agg(row_to_json(t)) \
  FROM (SELECT * FROM patch_message) t;" \
  -t -A > ../frontend/data/patch_message.json
