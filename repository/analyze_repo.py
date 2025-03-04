import os
import re
import json
from git import Repo
from concurrent.futures import ProcessPoolExecutor, as_completed

# Global variable to store the repo handle per worker
global_repo = None

def init_worker(repo_path):
    """
    Initialize each worker by opening the repository only once.
    """
    global global_repo
    global_repo = Repo(os.path.expanduser(repo_path))

def extract_commit_associations(commit):
    """
    Extract associated people from the commit message.
    Looks for lines starting with one of these keys (case-insensitive):
      - Author:
      - Reported-by:
      - Reviewed-by:
      - Co-authored-by:
    Returns a list of tuples (name, email, association_type).
    """
    associations = []
    assoc_keys = ["Author", "Reported-by", "Reviewed-by", "Co-authored-by"]
    pattern = re.compile(
        r'^(%s):\s+(.*?)(\s+<([^>]+)>)?\s*$' % '|'.join(assoc_keys),
        re.IGNORECASE | re.MULTILINE
    )
    for match in pattern.finditer(commit.message):
        assoc_type = match.group(1).strip()
        name = match.group(2).strip()
        email = match.group(4).strip() if match.group(4) else 'no_email@none.com'
        associations.append((name, email, assoc_type))
    return associations

def process_commit(commit_hexsha):
    """
    Process a single commit using the global repository handle.
    Extract associations, stats, and return a list of records.
    """
    commit = global_repo.commit(commit_hexsha)

    # Extract associations from the commit message.
    associations = extract_commit_associations(commit)
    # Always include commit.author entry.
    associations.append((commit.author.name, commit.author.email, "Commit Author"))
    
    stats = commit.stats.files
    commit_date_iso = commit.committed_datetime.isoformat()
    records = []

    for filepath, file_stats in stats.items():
        additions = file_stats.get('insertions', 0)
        deletions = file_stats.get('deletions', 0)
        for name, email, assoc_type in associations:
            person_str = f"{name} <{email}>"
            records.append([
                person_str,
                filepath,
                additions,
                deletions,
                commit.hexsha,
                commit_date_iso,
                assoc_type
            ])
    return records

def collect_repo_history(repo_path, output_path, max_workers=4):
    """
    Collect repository history in parallel using a process pool.
    Uses an initializer to avoid re-opening the repository on every commit.
    """
    # Open the repository once in the main process to get commit hexshas
    repo = Repo(os.path.expanduser(repo_path))
    commit_hexshas = [commit.hexsha for commit in repo.iter_commits('master')]
    history_data = []

    with ProcessPoolExecutor(max_workers=max_workers,
                             initializer=init_worker,
                             initargs=(repo_path,)) as executor:
        futures = {executor.submit(process_commit, hexsha): hexsha for hexsha in commit_hexshas}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                history_data.extend(result)
            except Exception as e:
                print(f"Error processing commit {futures[future]}: {e}")
            if i % 1000 == 0:
                print(f"Processed {i}/{len(commit_hexshas)} commits")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, indent=2)
    print(f"Done! Wrote {len(history_data)} records to {output_path}")

if __name__ == "__main__":
    repo_path = "~/postgres/postgres"  # Path to your repository
    output_path = "repo_history.json"  # Output JSON file
    collect_repo_history(repo_path, output_path)
