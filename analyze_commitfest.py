
from scrape import extract_commitfest_patch_ids, get_patch_info
from summarize_thread import explain_thread
from worker import run_jobs
from write_csv import dict_to_csv
from pprint import pprint


def analyze_commitfest(id):  
    #1. Scrape the list of patches.
    url = f"https://commitfest.postgresql.org/{id}/"
    patch_ids = extract_commitfest_patch_ids(url)

    print(patch_ids)

    # Scrape patches  in parallel.
    patch_info = run_jobs(get_patch_info, patch_ids, 5)
    pprint(patch_info)

    message_ids = [message_id for patch in patch_info.values() for message_id in patch['message_ids']]
    thread_summaries = run_jobs(explain_thread, message_ids, max_workers=5)

    # Write patch and thread data to files for future analysis
    dict_to_csv(patch_info, "patches.csv")
    dict_to_csv(thread_summaries, "thread_summaries.csv")

if __name__ == '__main__':
    analyze_commitfest(52)