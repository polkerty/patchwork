from dotenv import load_dotenv
import requests
import os

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



def explain_thread():


    pass

if __name__ == '__main__':
    q = prompt_gemini("What is most people's favorite color? Answer with a single word, the color, and do your best to pick the one right answer.")
    print(q)