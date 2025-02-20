
from scrape import extract_commitfest_patch_ids

def analyze_commitfest(id):  
    #1. Scrape the list of patches.
    url = f"https://commitfest.postgresql.org/{id}/"
    patch_ids = extract_commitfest_patch_ids(url)

    print(patch_ids)

if __name__ == '__main__':
    analyze_commitfest(52)