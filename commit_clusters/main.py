from repo import get_threads_of_last_n_commits

def main():
    commits = get_threads_of_last_n_commits('~/postgres/postgres', 10000)

    for commit in commits:
        print(commit)

    print(len(commits))


if __name__ == "__main__":
    main()