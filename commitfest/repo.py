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

def repair_message_id(id: str, sha: str):
     # message IDs pasted into commit threads are often broken. 
     # one super-common case is to miss the last letter, which we can repair as follows:

     # the .coms
    repaired = id

    com_co_corruptions = [
         'gmail.co', 
         'google.co',
         'outlook.co', 
         'vmware.co',
         'qq.co',
         'leadboat.co',
         'depesz.co',
         'j-davis.co',
         'amazon.co',
         'dalibo.co',
         'exchangelabs.com',


    ]
    for site in com_co_corruptions:
          if id.endswith(site):
               repaired += 'm'
               break
          
    # other corrections
    for suffix in [
         '.compute.internal',
         '.org',
         '.ru',
         'paquier.xyz',
         'aivenlaptop',
         'alvherre.pgsql',
         'nttdata.com',
         '.co.jp',
         'Spark',
         '.pa.us',
         '.net',
         '.de',
         'momjian.us',
         'vondra.me',
         'OUTLOOK.COM',
         'nathan',
         'neon.tech',
         'proxel.se',
         'woodcraft.me.uk',



    ]:
         if id.endswith(suffix[:-1]):
              repaired += suffix[-1]
              break

    if id != repaired:
         print(sha, f"Fixed ID: {id} -> {repaired}")

    return repaired
    

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
