from dotenv import load_dotenv
import requests
import os
from scrape import parse_thread, _helper_extract_attachment_links
from datetime import datetime
import json
from pprint import pprint
from cache import cache_results
import re

load_dotenv()


def prompt_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Must provide GEMINI_API_KEY env variable")
   
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
   
    res = requests.post(url, 
        json={
        "contents": [{
             "parts":[{"text": prompt}]
            }]
        }, 
        headers={ 'Content-Type': 'application/json' }
    ).json()

    ans = res["candidates"][0]["content"]["parts"][0]["text"] # I try not to design schemas, but when I do, I hide the actual result six levels deep.

    return ans

# Gemini loves wrapping its JSON in a "```json ```", no matter what we tell it, so try stripping this out if it's present.
def clean_gemini_json(json_string: str):
    # Regular expression to detect JSON wrapped with backticks and json indicator
    match = re.search(r'^```json\n(.*)\n```$', json_string, re.DOTALL)
    
    # If wrapped, extract the inner JSON part
    if match:
        json_string = match.group(1)
    
    # Parse the JSON and return as a dictionary
    return json.loads(json_string)

def analyze_thread(thread_id):
    text, attachment_links, from_and_date_list = parse_thread(thread_id)

    explanation = explain_thread(text, thread_id)

    last_activity = from_and_date_list[-1][1] # given that there is a mailing thread at all, there must be at least one entry.
    author = from_and_date_list[0][0]
    reviewer_list = list(set([name for name, date in from_and_date_list if name != author]))

    stats = {
        "last_activity": last_activity,
        "author": author,
        "reviewer_list": json.dumps(reviewer_list) # for frontend use
    }

    return {
        "explanation": explanation,
        "attachment_links": attachment_links,
        "stats": stats
    }
    

@cache_results(1)
def explain_thread(text, thread_id): # thread_id argument used for cacheing

    prompt = f'''
        You are an intelligent database developer and community manager. You are to be given a mailing list thread which will contain
        a series of emails discussing a particular proposed patch to the Postgresql database. You should read the full thread and note the following:

        1. What is the purpose of the proposed patch or feature, stated briefly but precisely in 1-3 sentences? 
            This will usually be laid out in the first email, but take into account any
            relevant changes agreed on in later emails.
        2. What is the state of the discussion? This should correspond to one of the following enums:
            * WAITING_ON_AUTHOR (that is, changes have  been requested from the author, and we are still waiting for the author to follow up); 
            * WAITING_FOR_COMMITTER (a committer has indicated that the patch is ready to go, but it doesn't appear that the patch has actually been committed yet)
            * DONE (it has been confirmed that the patch has been committed)
            * WAITING_FOR_REVIEW (the author is waiting on additional feedback to proceed)
            * LACKS_SUPPORT (there is strong pushback on the overall nature or purpose of the patch, and there is no resolution to that pushback)

            To help you distinguish between WAITING_ON_AUTHOR and WAITING_FOR_REVIEW, take special note of the email that sent the first
            message and the email that sent the most recent message. If they are the same, then likely we're waiting on a reviewer,
            not on the author, unless the latest message is a promise from the author to follow up with additional changes.
            Most of the time, if the latest message contains patches for review, then we are waiting for a reviewer, not for the author, 
            as well.

        3. In addition, consider the timestamps of the latest developments on the thread, relative to the current date ({datetime.now()}). If there is an active
            discussion over the last few weeks, classify the thread as ACTIVE, otherwise (if it appears that discussion has petered off, without
            much ongoing discussion or activity, particularly on the part of the original author) classify the thread as INACTIVE.
        4. What is the overall complexity of the feature or change? Imagine you are trying to rate this for the benefit of a code reviewer. 
            Rate the complexity on a scale from 1 to 5 where:
            * 1 is, perhaps, a change to a comment or other non-functional adjustment, and 
            * 2 is a small functional change, perhaps a minor adjustment to a single function;
            * 3 is still a relatively small feature but probably involves changing multiple files and functions.
            * 4 is a medium-size change that requires substantial understanding of postgres internals to review. It may interact with key
                parts of the database like the WAL, but is still more of an enhancement than a foundational refactor.
            * 5 is a deep refactor of a fundamental system or a major new feature.  
        5. In one or two sentences, what is the biggest issue or question currently outstanding? If this is not  relevant (for example, the proposal
            has already been committed), this can just be "N/A".
        6. Based on your subjective review of the mailing list thread, do you believe it would be a good use of time for an ADDITIONAL reviewer to spend some time
            reviewing and providing feedback? You might answer "NO" if it appears the author had not been responding, if substantial problems
            have already been pointed out, if there is already a reviewer who appears actively engaged, or for any other reason. 
            On the other hand, if the patch appears to be reasonable and mostly
            just needs someone to continue to review it, and there is no reviewer who is still actively engaged,
            you would reply "YES".  

            Just to be clear on this point, if there are already one or more reviewers who are actively providing feedback, especially if we 
            are currently waiting on the author instead of a reviewer, we should most likely say "NO" here. However, if the feature appears
            especially complex and existing reviewers have not engaged thoroughly with it, perhaps only giving nitpicks instead of deep reviews
            on the substance, you might respond "YES" here. Also, if we are waiting for a review on the most recent patches
            and it's been more than a few days, we should probably say "YES".  

        After you review the mailing list below, please respond with a JSON object in the following format, corresponding to the 4 categories above:

        {{
            "summary": "latest summary of proposal",
            "status": "one of WAITING_ON_AUTHOR|WAITING_FOR_COMMITTER|DONE|WAITING_FOR_REVIEW|LACKS_SUPPORT",
            "activity": "one of ACTIVE|INACTIVE",
            "complexity": <a number from 1 to 5>,
            "problem": "the key issue currently being discussed in the thread, if any",
            "wouldBenefitFromNewReviewer": "YES|NO"

        }}

        Here is the test of the mailing list:

        { text }

        -- 

        Now that you have read the thread, please respond with a JSON object as requested above, in the following format:

        {{
            "summary": "latest summary of proposal",
            "status": "one of WAITING_ON_AUTHOR|WAITING_FOR_COMMITTER|DONE|WAITING_FOR_REVIEW|LACKS_SUPPORT",
            "activity": "one of ACTIVE|INACTIVE",
            "complexity": <a number from 1 to 5>,
            "problem": "the key issue currently being discussed in the thread, if any",
            "wouldBenefitFromNewReviewer": "YES|NO"
        }}

        Respond ONLY with JSON, with no additional characters or text, so we can parse the response. The first character of your output should be {{,
        and the last character should be }}. Do NOT include any backticks around the JSON or additional annotation indicating the response is JSON,
        since we can't parse that.

        I repeat: DO NOT INCLUDE ANY OUTPUT, INCLUDING BACKTICKS, BEYOND THE JSON ITSELF.

    '''

    summary = prompt_gemini(prompt)

    try:
        parsed = clean_gemini_json(summary)
        return parsed
    except:
        print(summary)
        raise ValueError("Unable to parse LLM response as JSON")


if __name__ == '__main__':
    explanation = explain_thread("415721CE-7D2E-4B74-B5D9-1950083BA03E@yesql.se")
    pprint(explanation)