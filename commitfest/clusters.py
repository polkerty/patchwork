from repo import get_threads_of_last_n_commits
from analyze_thread import parse_thread, summarize_thread_for_predicting_committer
from tf_idf import compute_tfidf_top_terms
from predict_committer import train_committer_model

from cache import cache_results
from worker import run_jobs

from collections import Counter

@cache_results()
def get_valid_repo_threads(repo, commits):
    commit_and_thread = get_threads_of_last_n_commits(repo, commits)

    committer_of_thread = {
        ct['thread']: ct['author'] for ct in commit_and_thread
    }

    # 2. fetch threads
    message_ids = [t["thread"] for t in commit_and_thread]
    # this will fetch a cache that includes the text of the thread
    threads = run_jobs(parse_thread, message_ids, max_workers=5) # hopefully won't get throttled at this low rate

    # simply discard threads that failed because of a 404 or other reason
    valid_threads = {thread: results[0] for thread, results in threads.items() if 'error' not in results}
    print(f"Success rate in threads: {len(valid_threads)}/{len(threads)} ({round(100 * len(valid_threads)/len(threads))}%).")
    
    return [[
        text,
        committer_of_thread[thread],
        thread
    ] for thread, text in valid_threads.items()]

def main():
    threads = get_valid_repo_threads('~/postgres/postgres', 10000)

    print(f'Got {len(threads)} threads')
    print(threads[0])

    top_committers = Counter([committers for text, committers, thread in threads])
    for item, count in top_committers.most_common():
        print(f'{item}\t{count}')

    # only consider committers with at least 50 commits
    threads_by_active_committers = [(text, committer, thread) for text, committer, thread in threads if top_committers[committer] >= 50]

    # with open('skip_terms.txt', 'r') as skip_file:
    #     skip_terms = skip_file.read().split('\n')
    
    # print("Terms to skip: ", skip_terms)

    # start with just a little data
    threads_by_active_committers = threads_by_active_committers[:1000]

    # now, summarize the threads.
    summarized_threads = run_jobs(
        summarize_thread_for_predicting_committer, 
        threads_by_active_committers,
        max_workers=10,
        payload_arg_key_fn= lambda x: x[2]
    )

    for thread_id, summary in summarized_threads.items():
        print(thread_id, summary)

    training_data = [(summarized_threads[thread], committer) for _text, committer, thread in threads_by_active_committers ]
    train_committer_model(training_data)

    # terms = compute_tfidf_top_terms(threads, 1000)
    # # for manual inspection
    # for term in terms:
    #     print(f'{term[0]}\t{float(term[1])}')


if __name__ == "__main__":
    main()