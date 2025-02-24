from repo import get_threads_of_last_n_commits
from analyze_thread import parse_thread
from worker import run_jobs

def main():
    # 1. Get thread ids
    commit_and_thread = get_threads_of_last_n_commits('~/postgres/postgres', 10000)

    print(f'Got {len(commit_and_thread)} threads')
    print(commit_and_thread[0]) # sample

    # 2. fetch threads
    message_ids = [t["thread"] for t in commit_and_thread]
    # this will fetch a cache that includes the text of the thread
    threads = run_jobs(parse_thread, message_ids, max_workers=5) # hopefully won't get throttled at this low rate

if __name__ == "__main__":
    main()