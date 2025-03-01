

from scrape import fetch_thread
from llm import prompt_gemini, clean_gemini_json
from cache import cache_results
from worker import run_jobs

import requests
from bs4 import BeautifulSoup

from pprint import pprint
from datetime import datetime, timezone
import re
import json

PATCH_TOO_LARGE = 'patch_too_large_for_analysis'

'''
1. Author
2. Is author a committer? (could be an extra circle around the dot, or something)
3. Summary
4. Dependencies on earlier emails
5. Date
6. Has patches?
7. Patch stats (file names and + -)
8. Complexity of patches: minor | medium | major 
9. Status: { APPROVAL | REQUEST CHANGES | PATCHSET | OTHER }

'''
def describe_message(args):
    (key, contents) = args
    header = describe_header(contents['header'])
    body = describe_body(key, contents['body'])

    if 'attachments' in contents:
        attachments = list_attachments(contents['attachments'])
    else:
        attachments = None

    if attachments:
        with_position = [(pos, attachment) for (pos, attachment) in enumerate(attachments)]
        descriptions = run_jobs(describe_attachment, with_position, 5, payload_arg_key_fn=lambda x: x[0])
        for pos, description in descriptions.items():
            attachments[pos]['description'] = description

    return {
        "key": key,
        "header": header,
        "body": body,
        "attachments": attachments,
        "contents": contents
    }


# Get author and date
def describe_header(html_str):
    """
    Parse the message header HTML and return a dict with:
      - author: the 'From' name (no email address)
      - sent_utc: an ISO8601 UTC date string (e.g., '2014-10-10T07:57:56Z')
    """
    soup = BeautifulSoup(html_str, "html.parser")
    
    # Initialize results
    author = None
    sent_utc = None
    
    # Each row is <tr> with a <th scope="row"> label and a <td> value
    for row in soup.find_all('tr'):
        th = row.find('th', scope='row')
        td = row.find('td')
        if not th or not td:
            continue
        
        label = th.get_text(strip=True)
        value = td.get_text(strip=True)
        
        if label == "From:":
            # 'Andres Freund <andres(at)2ndquadrant(dot)com>'
            # We just want the name portion, so split on '<'
            # or, if there's no bracket, just take the entire string.
            # e.g., "Andres Freund <andres(at)2ndquadrant(dot)com>"
            bracket_index = value.find('<')
            if bracket_index != -1:
                author = value[:bracket_index].strip()
            else:
                author = value.strip()
                
        elif label == "Date:":
            # '2014-10-10 07:57:56'
            # Assume this is already UTC
            # Convert to an ISO8601 string with trailing Z
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            dt_utc = dt.replace(tzinfo=timezone.utc)
            sent_utc = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "author": author,
        "sent_utc": sent_utc
    }


# Describe message and determine what kind of response it is
@cache_results(0)
def describe_body(key, contents):

    prompt = f'''
        You are reading an email in a mailing list thread that discusses 
        a potential feature for the Postgres database. 

        You should output a JSON with the following 2 components:
        1. A one-sentence summary of the email (we'll use this to overview the thread itself.)
        2. The status of the email. This should be one of the following:
            * PATCH_SET --> The email itself contains some additional patches. 
            * REQUEST_CHANGES --> The email provides feedback on an earlier proposal, requesting some changes.
            * APPROVAL --> Implies the email is simply approving an earlier proposal. 
            * CLARIFICATION --> Implies the email is answering an earlier question. 
            * QUESTION --> Implies the email is asking a question. 
            * SUPPORT --> Implies the email is primarily expressing support for the proposed feature (but is not 
                an actual review, otherwise we would use APPROVAL here).
            * OTHER --> none of these statuses is a good fit.

            Note that these statuses are in precedence order: If an email requests some changes AND includes
            a patch-set, we should call it a "PATCH_SET". If the email approves some changes and requests changes
            in others, we should call it a "REQUEST_CHANGES", not "APPROVAL", and so on.

        Here is the body of the email: 

        { 
            contents
        }

        Please output your verdict as a JSON with no other commentary so we can parse it cleanly. Your first character should be a 
        {{ and your last, also a }}. The format should be:

        {{
            "summary": "one-line summary of email",
            "status": "PATCH_SET|REQUEST_CHANGES|APPROVAL|OTHER"
        }}

    '''
    
    result = prompt_gemini(prompt)

    return clean_gemini_json(result)

def parse_size_to_bytes(size_str):
    """
    Parse a human-readable file size string (e.g., '11.0 KB', '2.9 MB')
    into an integer number of bytes.
    """
    # Replace non-breaking spaces and strip whitespace.
    size_str = size_str.replace('\xa0', ' ').strip()
    if not size_str:
        return 0

    parts = size_str.split()
    if len(parts) < 2:
        # If there's no clear unit (just a number?), treat it as bytes
        try:
            return int(parts[0])
        except ValueError:
            return 0

    try:
        # Numeric part
        value = float(parts[0])
        # Unit part
        unit = parts[1].lower()
    except ValueError:
        return 0

    # Map from unit to multiplier
    multipliers = {
        'b': 1,
        'bytes': 1,
        'kb': 1024,
        'mb': 1024 ** 2,
        'gb': 1024 ** 3
    }

    # If the unit is not recognized, we'll assume bytes.
    multiplier = multipliers.get(unit, 1)
    return int(value * multiplier)


def list_attachments(html_snippet):
    """
    Parse the HTML snippet for the attachments table,
    returning a list of attachments with fields:
    name, url, size, contentType.

    Only returns attachments with content-type text/x-patch.
    Converts the human-readable size to an integer (bytes).
    """
    base_url = 'https://postgresql.org'
    soup = BeautifulSoup(html_snippet, "html.parser")
    attachments_table = soup.find("table", class_="message-attachments")
    if not attachments_table:
        return []
    
    attachments = []
    tbody = attachments_table.find("tbody")
    if not tbody:
        return []

    rows = tbody.find_all("tr")
    
    for row in rows:
        link_cell = row.find("th")
        link_tag = link_cell.find("a") if link_cell else None
        name = link_tag.text.strip() if link_tag else None
        url  = link_tag["href"] if link_tag and link_tag.has_attr("href") else None
        
        cells = row.find_all("td")
        if len(cells) != 2:
            continue
        
        content_type = cells[0].get_text(strip=True)
        size_str = cells[1].get_text(strip=True)
        
        # Filter only text/x-patch
        if content_type != "text/x-patch":
            continue
        
        # Convert size to bytes
        size_bytes = parse_size_to_bytes(size_str)
        
        attachments.append({
            "name": name,
            "url": base_url + url,
            "size": size_bytes,
            "contentType": content_type
        })
    
    return attachments


def describe_attachment(args):
    key, properties = args

    # 1. fetch the attachment
    contents = requests.get(properties["url"]).text

    ret = {
        "stats": parse_diff_stats(contents),
    }

    if len(contents) < 50000:
        prompt = f'''
            You are reading a Git patch diff to Postgres. We would like you to decide the following things about it:

            1. How complex is this change? Respond on a scale of 1 to 5, where
                * 1 is a small, non-functional change, like editing a typo in a comment
                * 2 is minor functional change, perhaps adding a small bit of functionality,
                    but with a low risk of breaking anything.
                * 3 is a medium-size change, perhaps changing some existing functionality 
                * 4 is a substantial change, touching many files and/or changing critical parts
                    of the codebase in ways that are tricky to reason about.
                * 5 is at the far end of complexity - something truly complex and ambitious
                    that would be very difficult to test and review. 

            2. In your judgement, what level of readiness is this patch for review? (1 - 3)
                * 1: The patch is in a preliminary, WIP condition, definitely not ready for 
                    a full review. Look for comments indicating TODOs, WIPs,
                    and so on, for example.
                * 2: The patch is ready for review, but there may be some rough edges. 
                * 3: The patch looks polished, well-commented, and looks read to commit to 
                    the codebase.

            Here is the contents of the git patch: 
            ```
            { 
                contents
            }
            ```
            Please output your verdict as a JSON with no other commentary so we can parse it cleanly. Your first character should be a 
            {{ and your last, also a }}. The format should be:

            {{
                "complexity": <1 to 5>,
                "readiness": <1 to 3>
            }}

        '''
        
        result = prompt_gemini(prompt)

        cleaned_result = clean_gemini_json(result)

        ret["analysis"] = cleaned_result

    return ret



'''
The mailing list lays out components of each email at the same level, like so:

<table class="message-header" ></table>
<div class="message-content" ></div>
<table class="message-attachments" ></table>

This method packages components of the same email together.
'''

def parse_messages(soup):
    wrap = soup.find(id="pgContentWrap")
    if wrap is None:
        raise ValueError("Could not find wrapper")

    top_elems = wrap.find_all(["table", "div"], recursive=False)
    
    messages = []
    current_message = {}
    
    # The first header table is not part of a message
    first_table_ignored = False

    for element in top_elems:
        # If we haven't ignored the first table yet and this is a table, skip it.
        if element.name == "table" and not first_table_ignored:
            first_table_ignored = True
            continue
        
        classes = element.get("class", [])
        
        if "message-header" in classes:
            # If there's an existing message in the pipeline, finalize it
            if "header" in current_message:
                messages.append(current_message)
                current_message = {}
            current_message["header"] = str(element)
        
        elif "message-content" in classes:
            current_message["body"] = str(element)
        
        elif "message-attachments" in classes:
            current_message["attachments"] = str(element)
    
    # If we ended with a partial message, finalize it
    if "header" in current_message:
        messages.append(current_message)
    
    return messages


def parse_diff_stats(diff_text: str):
    """
    Parse a git diff/patch file and return:
      - total number of files changed
      - total lines added
      - total lines deleted
    """

    file_count = 0
    total_additions = 0
    total_deletions = 0

    for line in diff_text.splitlines():
        # Each file change typically starts with 'diff --git a/... b/...'
        if line.startswith("diff --git"):
            file_count += 1
        
        # Count additions and deletions
        elif line.startswith("+") and not line.startswith("+++"):
            total_additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            total_deletions += 1

    return {
            "files": file_count, 
            "additions": total_additions,
            "deletions": total_deletions
    }

def trace_thread_references(thread):

    line_source = {}

    for message in thread:
        text = message['contents']['body']
        message['references'] = []
        lines = parse_email_snippet(text)

        for is_quoted, line in lines:
            if len(line) < 20:
                continue # ignore short lines
            if not is_quoted and line not in line_source:
                line_source[line] = message['key']
            elif is_quoted and line in line_source:
                message['references'].append(line_source[line])

        message['references'] = list(set(message['references']))


def parse_email_snippet(html_snippet: str) -> list[tuple[bool, str]]:
    """
    Parse an HTML snippet from an email, returning a list of (is_quote, line_text) tuples.

    :param html_snippet: The HTML email snippet to parse
    :return: A list of (is_quote, line_text) tuples
    """
    soup = BeautifulSoup(html_snippet, "html.parser")
    # Use get_text with a separator so <br/> becomes newlines.
    all_text = soup.get_text("\n")

    lines = []
    for raw_line in all_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue  # Skip blank lines if desired.

        # Check if line starts with one or more '>' characters.
        match = re.match(r"^>+", line)
        if match:
            # It's a quote. Remove all leading '>' chars and surrounding spaces.
            stripped_line = re.sub(r"^>+", "", line).strip()
            lines.append((True, stripped_line))
        else:
            # Not a quote
            lines.append((False, line))

    return lines

@cache_results()
def tell_thread_story(thread_id):
    # 1. Load thread text
    text = fetch_thread(thread_id)
    soup = BeautifulSoup(text, "html.parser")

    message_components = parse_messages(soup)
    messages_with_ids = [ ((thread_id, index), components) for index, components in enumerate(message_components)  ]

    messages = run_jobs(describe_message, messages_with_ids, 10, payload_arg_key_fn= lambda x: (x[0]))

    thread = [message for (_, message) in sorted(messages.items(), key= lambda x: x[0][1])]

    # now we want to check for messages that reference earlier messages
    trace_thread_references(thread)

    results = [{key: value for key, value in message.items() if key not in ("contents",)} for message in thread ]

    return results

@cache_results(0, 0)
def rank_for_beginners(args):

    thread, story = args

    prompt = f'''

    You are going to evaluate a patch in Postgres to see if it's a good fit for a first-time reviewer.

    To do that, I'm going to give you a summary of the mailing list for the thread. There is one
    entry per message, in chronological order, and you'll see when the messages were posted,
    who the author was, a summary of the message, and summary of any patches attached to that message,
    where we will tell you the number of bytes in the patch and also usually two scores:
        * complexity, from 1 to 5, where lower is easier to review, and
        * readiness, from 1 to 3, where lower is less ready to commit and higher is more ready.    

    Here are some overall factors to consider in deciding if a thread would benefit from
    having a relatively new reviewer look at it:


        * who is already involved and how involved are they? if someone has posted 2 detailed reviews in the last week, it's unlikely to be useful for another reviewer to show up ... but if they posted 2 messages and one said "add this to the CommitFest" and the second one further clarified how that works and said they hoped someone had timet to review, that might be interesting. also if somebody was reviewing a year ago and then stopped that's different than if it happened last week.

        * whose feedback would actually be useful? I think this one is probably quite tricky, but it seems to me that once senior people are fairly heavily involved, less experienced people are not likely to be as useful, except in specific circumstances - e.g. the senior people only said "this is far from ready", gave some directional guidance, and left; or if there's a question of desirability. it would actually be great to have some way to get more eyes on patches where there is a question of desirability, where what we need is as much an opinion as a review. but we'd somehow like to segregate patches that need a very senior person to resolve some difficult question from patches that need more normal review.
the ideal patch for a new person is one that's not a deeply bad idea in some way, not huge, not broken by design, and doesn't already have a complicated status with lots of context where many senior people have already said many interesting things.


    Now, here is the summary of the thread: 

    ```

        { 

            '\n * '.join([json.dumps(message) for message in story])
        }
    ```

    Please output a score from 0 to 10 indicating how much the thread would benefit from a new reviewer,
    where 0 = not at all and 10 = great fit, and also a short explanation of your reasoning, as a json in the following
    format:

    {{
        "explanation": "text",
        "score": <1 to 10>,

    }} 

    output no other text so that we can parse your response as a JSON; the first character should be {{ and
    the last should be }}.

    '''

    result = prompt_gemini(prompt)

    return clean_gemini_json(result)


def main():
    thread = '20130926225545.GB26663@awork2.anarazel.de'
    story = tell_thread_story(thread)

    for message in story:
        print(message)

    beginner_rank = rank_for_beginners(thread, story)
    print(beginner_rank)

if __name__ == '__main__':
    main()