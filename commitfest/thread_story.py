

from scrape import fetch_thread
from llm import prompt_gemini, clean_gemini_json
from cache import cache_results
from worker import run_jobs

from bs4 import BeautifulSoup
from pprint import pprint
from datetime import datetime, timezone

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
        attachments = describe_attachments(contents['attachments'])
    else:
        attachments = None

    return (header, body, attachments)


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

def describe_attachments(contents):
    pass



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


def tell_thread_story(thread_id):
    # 1. Load thread text
    text = fetch_thread(thread_id)
    soup = BeautifulSoup(text, "html.parser")

    message_components = parse_messages(soup)
    messages_with_ids = [ ((thread_id, index), components) for index, components in enumerate(message_components)  ]

    messages = run_jobs(describe_message, messages_with_ids, 25, payload_arg_key_fn= lambda x: (x[0]))

    # 2. We'll parse the text ourselves, because we want to do additional analysis
    # message_elements = soup.select('.message-content')
    # message_descriptions = [describe_message(message) for message in message_elements]

    # author_and_date = _helper_extract_from_and_date(soup)

    for pos, message in sorted(messages.items(), key= lambda x: x[0][1]):
        pprint(message)



def main():
    tell_thread_story('20130926225545.GB26663@awork2.anarazel.de')

if __name__ == '__main__':
    main()