from concurrent.futures import ThreadPoolExecutor, as_completed


def run_jobs(fn, payloads, max_workers=5, payload_arg_key_fn=None):
    results = {}
    errors = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        job_to_args = {executor.submit(fn, args): args for args in payloads}

        for job in as_completed(job_to_args):
            args = job_to_args[job]
            if payload_arg_key_fn:
                key = payload_arg_key_fn(args)
            else:
                key = args
            try:
                results[key] = job.result()
            except Exception as e:
                print(e)
                results[key] = {"error": str(e)}
                errors += 1

            print(f"Progress: {len(results)}/{len(payloads)} | Errors: {errors}")

    return results

