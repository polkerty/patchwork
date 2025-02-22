import requests
from cache import cache_results

@cache_results()
def analyze_attachment(link_and_message_id):

    link, message_id = link_and_message_id
    absolute_url = 'https://postgresql.org/' + link
    data = requests.get(absolute_url).text

    stats = parse_git_patch(data, link, message_id)

    return stats


def parse_git_patch(patch_content, diff_link, message_id):
    """
    Parse a Git patch string and extract file-level statistics: filename,
    number of additions, and number of deletions.

    :param patch_content: A string containing the contents of a .patch file.
    :return: A list of dictionaries. Each dictionary has:
        {
        'file': <filename (relative)>,
        'additions': <number of added lines>,
        'deletions': <number of deleted lines>,
        'link': <url of diff file itself>
        'message_id': <id of source thread>
        }
    """
    # Split the patch by lines
    lines = patch_content.splitlines()

    # We'll store the result in a list of dicts
    files_changed = []

    # Temporary trackers
    current_file = None
    additions = 0
    deletions = 0

    for line in lines:
        # Detect the start of a new file diff
        if line.startswith("diff --git "):
            # If we were processing a previous file, record its stats first
            if current_file is not None:
                files_changed.append({
                    'file': current_file,
                    'additions': additions,
                    'deletions': deletions,
                    'link': diff_link,
                    'message_id': message_id,
                })

            # Reset counters for the new file
            additions = 0
            deletions = 0

            # Parse the filename from the "diff --git a/... b/..."
            # Example line: "diff --git a/foo.py b/foo.py"
            # We'll assume the right-hand side filename is the "new" file.
            parts = line.split()
            # parts[-2] is something like 'a/foo.py'
            # parts[-1] is something like 'b/foo.py'
            # We can strip off the "b/" prefix to get the real filename.
            file_path = parts[-1][2:]  # remove "b/"
            current_file = file_path

        # Hunk metadata lines start with "@@", so ignore them
        # Lines beginning with "+++" or "---" indicate the old/new version references, also ignore
        elif line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
            continue

        # Actual changed lines:
        else:
            # Lines that are additions start with '+'
            if line.startswith('+'):
                # Ignore lines like "+++" (already covered above), so check length
                if len(line) > 1:
                    additions += 1

            # Lines that are deletions start with '-'
            elif line.startswith('-'):
                # Ignore lines like "---", so check length
                if len(line) > 1:
                    deletions += 1

    # If the patch didn't end with a new diff line, we might have leftover stats
    if current_file is not None:
        files_changed.append({
            'file': current_file,
            'additions': additions,
            'deletions': deletions,
            'link': diff_link,
            'message_id': message_id,
        })

    return files_changed