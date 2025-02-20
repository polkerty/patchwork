from dotenv import load_dotenv
import requests
import os
from scrape import scrape_text_from_div

load_dotenv()


def prompt_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Must provide GEMINI_API_KEY env variable")
   
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
   
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



def explain_thread(thread_id):
    url = f"https://www.postgresql.org/message-id/flat/{thread_id}"
    text = scrape_text_from_div(url, "pgContentWrap")

    print(text)




if __name__ == '__main__':
    explanation = explain_thread("b8a67d6dd34fe5e1b61272d11d40e5f576a00a0a.camel%40j-davis.com")