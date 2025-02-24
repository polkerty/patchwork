import re
from git import Repo

def get_last_n_commits(repo_path, n=5, branch='master'):
    """
    Returns the last N commits of the specified branch for a given repository path.

    :param repo_path: Path to the local git repository.
    :param n: Number of commits to fetch (default: 5).
    :param branch: Name of the branch to fetch commits from (default: "master").
    :return: A list of dictionaries, each containing 'author', 'commit_text', and 'date'.
    """
    repo = Repo(repo_path)
    
    # Retrieve commits from the specified branch
    commits = list(repo.iter_commits(branch, max_count=n))
    
    # Build a structured list of the desired commit info
    commit_list = []
    for commit in commits:
        commit_info = {
            'author': commit.author.name,
            'commit_text': commit.message.strip(),
            'date': commit.committed_datetime.isoformat(),
            'sha': commit.hexsha
        }
        commit_list.append(commit_info)
    
    return commit_list

def get_threads_of_last_n_commits(repo_path, n=5, branch='master'):
    commits = get_last_n_commits(repo_path, n, branch)

    results = []

    for commit in commits:
        regex = re.compile(r"https://postgr\.es/m(?:/flat)?/([^/\s]+)")
        threads = regex.findall(commit['commit_text'])

        if len(threads):
                for thread in threads:
                    results.append({
                        "sha": commit['sha'], 
                        "date": commit['date'], 
                        "thread": thread
                    })

    return results
