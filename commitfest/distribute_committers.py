import json

def main():
    pass


def prediction_score(prediction, target):
    for committer, rate, terms in prediction[1]:
        if target == committer:
            return rate

    return 0 # no match!

def get_entry(predictions, target):
    for committer, rate, terms in predictions:
        if target == committer:
            return (committer, rate, terms)

    return None # no match!

def fair_committer_assignments(data):
    predictions = data["predictions"]

    base_rates = data["base_rates"]

    print(base_rates)

    # first pass
    by_committer = {}
    by_thread = {}

    committers_freq_asc = sorted(list(base_rates.items()), key=lambda x:x[1])

    target_reviewers_per_patch = 3

    committers_by_thread = { thread: set() for thread in predictions}

    pass_count = 0
    while True:
        did_update = False

        # Each thread can be claimed only once per pass, to ensure fairness.
        taken = set()

        for committer, rate in committers_freq_asc:
            print(committer, rate)
            my_threads = sorted(list(predictions.items()), key=lambda x: prediction_score(x, committer), reverse=True)

            # For this reviewer, consider patches that:
            #  1. have not been claimed yet in this pass
            #  2. have never been claimed by this reviewer
            #  3. have open review slots
            #  4. have a positive association with this reviewer
            filtered = [
                thread for thread in my_threads 
                if thread[0] not in taken and 
                    committer not in committers_by_thread[thread[0]] and
                    len(committers_by_thread[thread[0]]) < target_reviewers_per_patch and
                    prediction_score(thread, committer) > 0
            ]

            # We restrict the number of claims per pass to be proportional
            # to the reviewer's baseline commit rate.
            limit = round(base_rates[committer] * len(predictions))
                        
            limited = filtered[:limit]

            if not committer in by_committer:
                by_committer[committer] = []

            for thread_id, thread_matches in limited:
                if not thread_id in by_thread:
                    by_thread[thread_id] = []
                taken.add(thread_id)
                committers_by_thread[thread_id].add(committer) # make sure we don't claim again
                c, score, terms = get_entry(thread_matches, committer)
                by_committer[committer].append((thread_id, score, terms))
                by_thread[thread_id].append((committer, score, terms))
                did_update = True

        pass_count += 1


        if not did_update:
            break
        
    return by_thread

if __name__ == '__main__':
    with open('extended_predictions.json', 'r') as f:
        data = json.load(f)

    
    fair_committer_assignments(data)