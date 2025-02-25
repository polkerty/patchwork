from repo import get_threads_of_last_n_commits
from analyze_thread import parse_thread
from tf_idf import compute_tfidf_top_terms

from cache import cache_results
from worker import run_jobs

from pprint import pprint

@cache_results()
def get_valid_repo_threads(repo, commits):
    commit_and_thread = get_threads_of_last_n_commits(repo, commits)

    # 2. fetch threads
    message_ids = [t["thread"] for t in commit_and_thread]
    # this will fetch a cache that includes the text of the thread
    threads = run_jobs(parse_thread, message_ids, max_workers=5) # hopefully won't get throttled at this low rate

    # simply discard threads that failed because of a 404 or other reason
    valid_threads = {thread: results for thread, results in threads.items() if 'error' not in results}
    print(f"Success rate in threads: {len(valid_threads)}/{len(threads)} ({round(100 * len(valid_threads)/len(threads))}%).")

    return valid_threads




def main():
    threads = get_valid_repo_threads('~/postgres/postgres', 10000)

    print(f'Got {len(threads)} threads')
    pprint(list(threads.items())[0]) # sample

    terms = compute_tfidf_top_terms(threads)
    for term in terms:
        print(term)


if __name__ == "__main__":
    main()