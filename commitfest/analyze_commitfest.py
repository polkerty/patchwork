
from scrape import extract_commitfest_patch_ids, get_patch_info
from analyze_thread import analyze_thread
from attachments import analyze_attachment
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
    threads = run_jobs(analyze_thread, message_ids, max_workers=5)

    thread_summaries = {id: thread["explanation"] for id, thread in threads.items()}
    attachment_links = {id: { "links": thread["attachment_links"] } for id, thread in threads.items()}

    # download attachments
    links_flattened = [ (link, message_id) for message_id, link_obj in attachment_links.items() for link_list in link_obj.values() for link in link_list ]
    attachment_stats  = run_jobs(analyze_attachment, links_flattened, max_workers=5)
    attachment_stats_flattened = { f'{link}/{stats["file"]}': stats for link, files in attachment_stats.items() for stats in files }

    print(attachment_stats_flattened)
    # Write patch and thread data to files for future analysis
    dict_to_csv(patch_info, "patches.csv")
    dict_to_csv(thread_summaries, "thread_summaries.csv")
    dict_to_csv(attachment_links, "attachment_links.csv")
    dict_to_csv(attachment_stats_flattened, "attachment_stats.csv")

if __name__ == '__main__':
    analyze_commitfest(52)