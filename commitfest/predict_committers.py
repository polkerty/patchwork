from repo import get_threads_of_last_n_commits
from analyze_thread import parse_thread, summarize_thread_for_predicting_committer
from committer_model import train_committer_model, predict_top_committers
from random import shuffle, seed

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

@cache_results()
def prepare_committer_training_data():
    threads = get_valid_repo_threads('~/postgres/postgres', 10000)

    print(f'Got {len(threads)} threads')
    print(threads[0])

    threads_of_valid_len = [t for t in threads if len(t[0]) < 3500000]
    print(f"Filtered out {len(threads) - len(threads_of_valid_len)} threads ({round(100*(len(threads)-len(threads_of_valid_len))/len(threads))}%)")

    top_committers = Counter([committers for text, committers, thread in threads_of_valid_len])
    for item, count in top_committers.most_common():
        print(f'{item}\t{count}')

    # only consider committers with at least 50 commits
    threads_by_active_committers = [(text, committer, thread) for text, committer, thread in threads_of_valid_len if top_committers[committer] >= 50]

    # with open('skip_terms.txt', 'r') as skip_file:
    #     skip_terms = skip_file.read().split('\n')
    
    # print("Terms to skip: ", skip_terms)

    # start with just a little data
    # threads_by_active_committers = threads_by_active_committers[:1000]

    # now, summarize the threads.
    summarized_threads = run_jobs(
        summarize_thread_for_predicting_committer, 
        threads_by_active_committers,
        max_workers=4,
        payload_arg_key_fn= lambda x: x[2]
    )

    for thread_id, summary in summarized_threads.items():
        print(thread_id, summary)

    training_data = [(summarized_threads[thread], committer) for _text, committer, thread in threads_by_active_committers ]

    return training_data

def predict_committers(thread_ids):
    # build model on the fly.
    # doesn't take too long once the training data
    # is downloaded and cached - but boy, that takes a while!
    print("Getting data to train commiitter prediction model...")
    seed("foo")
    training_data = prepare_committer_training_data()
    shuffle(training_data)
    print("Training committer prediction model...")
    model, vectorizer, _stats = train_committer_model(training_data)

    print("Downloading threads for committer model...")
    threads = run_jobs(parse_thread, thread_ids, max_workers=5)
    threads_flat = [[
        text,
        None, # this holds the committer in training, but of course we don't this here,
              # since it's what we're trying to predict!
        thread
    ] for thread, text in threads.items()]

    print("Extracting keywords from provided threads...")
    summarized_threads = run_jobs(
        summarize_thread_for_predicting_committer, 
        threads_flat,
        max_workers=4, # we're trying to stay under 4 million tokens/min, but not too far under.
                       # this seems experimentally to be a good setting. 
        payload_arg_key_fn= lambda x: x[2]
    )

    # And now we run the model. Not multithreaded yet
    predicted_committers = {}
    for thread, text in summarized_threads.items():
        prediction = predict_top_committers(model, vectorizer, text, 3)
        a, score_a = prediction[0]
        b, score_b = prediction[1]
        c, score_c = prediction[2]
        predicted_committers[thread] = {
            "a": a,
            "score_a": score_a,
            "b": b,
            "score_b": score_b,
            "c": c,
            "score_c": score_c
        }

    return predicted_committers


def main():
    seed("foo")
    training_data = prepare_committer_training_data()

    shuffle(training_data)
    train_committer_model(training_data)

    # terms = compute_tfidf_top_terms(threads, 1000)
    # # for manual inspection
    # for term in terms:
    #     print(f'{term[0]}\t{float(term[1])}')


if __name__ == "__main__":
    main()