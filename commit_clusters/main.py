from repo import get_last_n_commits
import re
def main():
    commits = get_last_n_commits('~/postgres/postgres', 10000)

    for commit in commits:
        regex = re.compile("https://postgr.es/m/(.*)\w")
        threads = regex.findall(commit['commit_text'])

        if len(threads):
                for i,  thread in enumerate(threads):
                    print (commit['sha'], commit['date'], thread, i)
        else:
             print(commit['sha'], commit['date'], None)


if __name__ == "__main__":
    main()