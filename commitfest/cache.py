import os
import json
import functools

CACHE_DIR = ".cache"
def cache_results(key=None, subkey=None):
    """Decorator to cache function results in a specified directory."""
    def decorator(func):
        os.makedirs(CACHE_DIR, exist_ok=True)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if key is None:
                suffix = f'{args}_{kwargs}'
            elif subkey is None:
                suffix = f'{list(args)[key]}'
            else:
                suffix = f'{list(args)[key][subkey]}'
            # Generate cache file path based on function name and arguments
            cache_key = f"{func.__name__}_{suffix}.json"
            cache_key = cache_key.replace("/", "_")  # Sanitize filenames
            cache_file = os.path.join(CACHE_DIR, cache_key)

            # Return cached result if available
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    print(f"Loaded from cache: {cache_key}")
                    return json.load(f)

            # Call the original function
            result = func(*args, **kwargs)

            # Save result to cache
            with open(cache_file, "w") as f:
                print(f"Wrote to cache: {cache_key}")
                json.dump(result, f)

            return result

        return wrapper
    return decorator
