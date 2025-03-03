import requests
from bs4 import BeautifulSoup
import re
from cache import cache_results

# Scraping the mailing list 
@cache_results()
def fetch_thread(id):
    url = f'https://www.postgresql.org/message-id/flat/{id}'

    response = requests.get(url)
    if response.status_code != 200:
        err = f"Failed to fetch the page for {id}: {response.status_code}"
        raise ValueError(err)

    return response.text

@cache_results()
def parse_thread(id):
    text = fetch_thread(id)
    soup = BeautifulSoup(text, "html.parser")

    main_text_id = 'pgContentWrap'
    
    # Find the div with the given id name
    div = soup.find("div", id=main_text_id)
    
    if div:
        text = div.get_text(separator="\n", strip=True)  # Extracts all text recursively
    else:
        raise ValueError(f"No div with id '{id}' found.")
    
    attachment_tables = soup.find_all("table", class_="message-attachments")

    if attachment_tables:
        # 2. Select the last table
        last_table = attachment_tables[-1]
        
        # 3. Find all <a> tags (with href) in this table
        anchors = last_table.find_all("a", href=True)

        links = [anchor["href"] for anchor in anchors]
    else:
        links = []

    from_and_date_list = _helper_extract_from_and_date(soup)

    return text, links, from_and_date_list

def _helper_extract_from_and_date(soup):
    """
    Given a BeautifulSoup object of the entire HTML document,
    find all message-header tables and extract the From name and Date
    from each table. Returns a list of tuples: [(from_name, date_str), ...].
    """

    def parse_email_header(table):
        """
        Given a BeautifulSoup <table> containing an email header,
        return a tuple (from_name, date_str).
        """
        from_th = table.find('th', string='From:')
        from_td = from_th.find_next('td') if from_th else None
        from_text = from_td.get_text(strip=True) if from_td else ""

        # Extract the name from something like:
        #   "\"Hayato Kuroda (Fujitsu)\" <kuroda(dot)hayato(at)fujitsu(dot)com>"
        match = re.match(r'^"([^"]+)"', from_text)
        if match:
            from_name = match.group(1)
        else:
            # If no quotes found, split at '<'
            from_name = from_text.split('<')[0].strip()

        date_th = table.find('th', string='Date:')
        date_td = date_th.find_next('td') if date_th else None
        date_str = date_td.get_text(strip=True) if date_td else ""

        return (from_name, date_str)

    results = []

    tables = soup.find_all('table', class_='table-sm table-responsive message-header')
    for t in tables:
        info = parse_email_header(t)
        if len(info[0]):
            results.append(info)
    return results



def _helper_extract_attachment_links(text):
    
    soup = BeautifulSoup(f'<html><body>{text}</body></html>', "html.parser")
    attachment_tables = soup.find_all("table", class_="message-attachments")

    if attachment_tables:
        # 2. Select the last table
        last_table = attachment_tables[-1]
        
        # 3. Find all <a> tags (with href) in this table
        links = last_table.find_all("a", href=True)

        return [link["href"] for link in links]
    else:
        return []

# Scraping the commitfest page
def parse_commitfest_page(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses


    # Get patch IDs
    soup = BeautifulSoup(response.text, 'html.parser')

    # Regex pattern to match the desired links
    pattern = re.compile(r'/patch/(\d+)/')

    # Find all links that match the pattern
    ids = []
    for a_tag in soup.find_all('a', href=True):
        match = pattern.match(a_tag['href'])
        if match:
            ids.append(int(match.group(1)))  # Extract and convert to int

    # Get contributor names
    authors = soup.find("select", id="id_author")

    option_texts = [option.get_text(strip=True) for option in authors.find_all("option")]
    parts_list = [name.split(' (') for name in option_texts]
    names = [parts[0] if len(parts) == 2 else None for parts in parts_list]
    authors = [name for name in names if name is not None]

    return ids, authors

# Scraping the Patch page
@cache_results()
def get_patch_info(patch_id):
    url = f'https://commitfest.postgresql.org/patch/{patch_id}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # We will extract the patches recursively from these later on
    message_ids = _helper_get_patch_message_ids(soup)
    name = _helper_get_patch_name(soup)

    return {
        "patch_id": patch_id,
        "message_ids": message_ids,
        "patch_name": name
    }

def _helper_get_patch_message_ids(soup):
    pattern = re.compile(r'https://www.postgresql.org/message-id/flat/(.*)')

    # Find all links that match the pattern
    ids = []
    for a_tag in soup.find_all('a', href=True):
        match = pattern.match(a_tag['href'])
        if match:
            ids.append(match.group(1)) 

    return list(set(ids))

def _helper_get_patch_name(soup):
    title = soup.find('h1')
    
    if title:
        return title.get_text(strip=True)
    return 'Title not found'


# get email bodies from thread for clustering.
def get_messages_from_thread(thread_text):
    """
    Takes an HTML snippet (no <html> or <body> tags) and returns a list
    of the text content from all elements with the 'message-content' class.
    """
    soup = BeautifulSoup(f'<html><body>{thread_text}</body></html>', 'html.parser')
    message_elements = soup.select('.message-content')
    return [element.get_text(strip=True) for element in message_elements]
