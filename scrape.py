import requests
from bs4 import BeautifulSoup
import re
from cache import cache_results

# Scraping the mailing list 

def scrape_text_from_div(url, id):
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch the page: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the div with the given id name
    div = soup.find("div", id=id)
    
    if div:
        return div.get_text(separator="\n", strip=True)  # Extracts all text recursively
    else:
        raise ValueError(f"No div with id '{id}' found.")

# Scraping the commitfest page
def extract_commitfest_patch_ids(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    soup = BeautifulSoup(response.text, 'html.parser')

    # Regex pattern to match the desired links
    pattern = re.compile(r'/patch/(\d+)/')

    # Find all links that match the pattern
    ids = []
    for a_tag in soup.find_all('a', href=True):
        match = pattern.match(a_tag['href'])
        if match:
            ids.append(int(match.group(1)))  # Extract and convert to int

    return ids

# Scraping the Patch page
@cache_results()
def get_patch_info(patch_id):
    url = f'https://commitfest.postgresql.org/patch/{patch_id}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    message_ids = _helper_get_patch_message_ids(soup)


    return {
        "patch_id": patch_id,
        "message_ids": message_ids,
    }

def _helper_get_patch_message_ids(soup):
    # Find the table row where <th> contains "Emails"

    message_ids = set()

    # Regex pattern to match the desired links
    pattern = re.compile(r'https://www.postgresql.org/message-id/flat/(.*)')

    # Find all links that match the pattern
    ids = []
    for a_tag in soup.find_all('a', href=True):
        match = pattern.match(a_tag['href'])
        if match:
            ids.append(match.group(1)) 

    return list(set(ids))


