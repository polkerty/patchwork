from dotenv import load_dotenv
import requests
import os
from time import sleep
from random import random
import re
import json

load_dotenv()


def prompt_gemini(prompt, attempt=0):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Must provide GEMINI_API_KEY env variable")
   
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
   
    req = requests.post(url, 
        json={
        "contents": [{
             "parts":[{"text": prompt}]
            }]
        }, 
        headers={ 'Content-Type': 'application/json' }
    ).json()

    try:
        ans = req["candidates"][0]["content"]["parts"][0]["text"] # I try not to design schemas, but when I do, I hide the actual result six levels deep.
    except Exception as e:
        if attempt < 10 and 'error' in req and 'code' in req['error'] and req['error']['code'] == 429:
            # backoff
            print(f"Retrying try #{attempt + 1}")
            sleep(5 * random() * 2**attempt )
            return prompt_gemini(prompt, attempt + 1)
        else:
            print("XX", "attempt=", attempt, "prompt len=", len(prompt), req) # for debugging
            raise e
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
