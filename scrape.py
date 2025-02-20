import requests
from bs4 import BeautifulSoup

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
