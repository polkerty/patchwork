
from scrape import extract_commitfest_patch_ids, get_patch_info
from worker import run_jobs
from pprint import pprint


def analyze_commitfest(id):  
    #1. Scrape the list of patches.
    url = f"https://commitfest.postgresql.org/{id}/"
    patch_ids = extract_commitfest_patch_ids(url)

    print(patch_ids)

    # Scrape patches  in parallel.
    patch_info = run_jobs(get_patch_info, patch_ids, 5)
    pprint(patch_info)



if __name__ == '__main__':
    analyze_commitfest(52)