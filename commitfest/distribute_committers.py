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

if __name__ == '__main__':
    with open('extended_predictions.json', 'r') as f:
        data = json.load(f)

    predictions = data["predictions"]

    base_rates = data["base_rates"]

    print(base_rates)

    print(list(predictions.items())[0])

    # first pass
    by_committer = {}
    taken = set()

    committers_freq_asc = sorted(list(base_rates.items()), key=lambda x:x[1])

    for committer, rate in committers_freq_asc:
        print(committer, rate)
        my_threads = sorted(list(predictions.items()), key=lambda x: prediction_score(x, committer), reverse=True)

        for thread in my_threads[:10]:
            print("\t", prediction_score(thread, committer))

        filtered = [thread for thread in my_threads if thread[0] not in taken and prediction_score(thread, committer) > 0]

        limit = round(base_rates[committer] * len(predictions))
                      
        print("\tLIMIT: ", limit, " out of ", len(predictions))

        limited = filtered[:limit]

        print("\tMATCH: ", len(limited))

        by_committer[committer] = []

        for thread_id, thread_matches in limited:
            taken.add(thread_id)
            c, score, terms = get_entry(thread_matches, committer)
            by_committer[committer].append((thread_id, score, terms))
            print("> ", thread_id, score, terms)


