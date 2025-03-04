import os
import re
import json
from git import Repo

def extract_commit_author(commit):
    """
    Look for an 'Author: XYZ <xyz@example.com>' line in the commit message.
    If found, return (name, email). Otherwise, fall back to commit.author.
    """
    # Regex to match: Author: Name <email@something>
    # This will capture the author's name in group(1) and email in group(2)
    author_override_regex = re.compile(r'^Author:\s+(.*?)(\s+<([^>]+)>)?', re.MULTILINE)
    match = author_override_regex.search(commit.message)

    if match:
        extracted_name = match.group(1).strip()
        extracted_email = match.group(2).strip() if match.group(2) else 'no_email@none.com'
        return extracted_name, extracted_email
    else:
        # Fallback to commit metadata
        return commit.author.name, commit.author.email

def collect_repo_history(repo_path, output_path):
    """
    Given the path to a Git repository, iterate through all commits and gather:
      - Author (possibly overridden by 'Author:' line in commit message)
      - Files changed
      - Lines added and deleted
      - Commit SHA

    Store the entire history as a list of lists, and write as JSON to output_path.
    """
    repo = Repo(repo_path)
    # In some cases you might want '--all' explicitly, or you can just do
    # `repo.iter_commits('--all')`
    all_commits = list(repo.iter_commits('master'))
    
    history_data = []

    pos = 0

    for commit in all_commits:
        # Extract overriding author if present
        author_name, author_email = extract_commit_author(commit)
        author_str = f"{author_name} <{author_email}>"

        # The commit stats has 'files' dict with file paths and insertions/deletions
        # commit.stats.files -> { 'path/to/file': { 'insertions': X, 'deletions': Y, ... }, ... }
        stats = commit.stats.files

        commit_date_iso = commit.committed_datetime.isoformat()

        # For each file changed in this commit, collect stats
        for filepath, file_stats in stats.items():
            additions = file_stats.get('insertions', 0)
            deletions = file_stats.get('deletions', 0)

            # Append a record in the requested format
            # [Author, Filepath, Additions, Deletions, CommitID]
            history_data.append([
                author_str,
                filepath,
                additions,
                deletions,
                commit.hexsha,
                commit_date_iso,
            ])

        pos += 1
        if pos % 1000 == 0:
            print(f"Progress: commit {pos} / {len(all_commits)} | Total file count: {len(history_data)}")
            # Write out to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2)

    print(f"Done! Wrote {len(history_data)} lines of commit-file history to {output_path}")

if __name__ == "__main__":
    # Path to the local cloned Git repository
    repo_path = "~/postgres/postgres"
    # Path where you want the JSON written
    output_path = "repo_history.json"

    collect_repo_history(repo_path, output_path)
