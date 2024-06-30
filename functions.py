from bs4 import BeautifulSoup
import json
import os
import spacy

# Function to load articles from a JSON file
def load_articles(filename='full_articles.json'):
    with open(filename, 'r') as f:
        return json.load(f)

# Load the spaCy model
def download_spacy_model():
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    return nlp

nlp = download_spacy_model()
# Load the articles from the JSON file
articles = load_articles('full_articles.json')
# List of keywords related to music
music_keywords = {
    "genres": ["rock", "pop", "jazz", "classical", "hip-hop", "electronic", "country", "blues", "metal"],
    "terms": ["song", "album", "artist", "band", "music", "track", "lyrics", "concert", "performance", "vinyl"],
    "instruments": ["guitar", "piano", "drums", "bass", "saxophone", "violin", "cello", "flute", "trumpet"],
    "hifi_gear": ["turntable", "amplifier", "speaker", "headphones", "phono preamp", "DAC", "receiver", "subwoofer", "cable"]
}

def extract_music_keywords(text):
    # Process the text using spaCy
    doc = nlp(text)

    # Extract tokens and named entities
    tokens = [token.text for token in doc]
    named_entities = [(ent.text, ent.label_) for ent in doc.ents]


    # Identify music-related keywords
    identified_keywords = {
        "tokens": [token for token in tokens if token.lower() in music_keywords["terms"]],
        "genres": [token for token in tokens if token.lower() in music_keywords["genres"]],
        "instruments": [token for token in tokens if token.lower() in music_keywords["instruments"]],
        "hifi_gear": [token for token in tokens if token.lower() in music_keywords["hifi_gear"]],
        "entities": [ent for ent in named_entities if ent[1] in ["PERSON", "ORG", "WORK_OF_ART", "DATE", "ORG", "GPE"]]
    }

    return identified_keywords

def append_relevant_articles(keywords, articles, messages):
    relevant_articles = search_articles(keywords, articles)
    for article in relevant_articles:
        content = article.get("content", "")
        if content:
            messages.append({"role": "system", "content": content})
    return messages

def flatten_keywords(keywords):
    flattened_keywords = []

    # Combine all keyword lists into a single list if they are not empty
    for key in ['tokens', 'genres', 'instruments', 'hifi_gear']:
        if keywords[key]:
            flattened_keywords += keywords[key]

    # Extract the entity names and add them to the flattened list if they are not empty
    if keywords['entities']:
        entity_names = [ent[0] for ent in keywords['entities']]
        flattened_keywords += entity_names

    # Remove "music" if it exists in the list
    flattened_keywords = [keyword for keyword in flattened_keywords if keyword.lower() != 'music']

    return flattened_keywords

def search_articles(keywords, articles):
    relevant_articles = []
    for article in articles:
        if any(keyword.lower() in article['title'].lower() for keyword in keywords):
            relevant_articles.append(article)
    return relevant_articles

def append_relevant_articles(keywords, articles, messages):
    relevant_articles = search_articles(keywords, articles)
    seen_articles = set()

    for article in relevant_articles:
        title = article.get("title", "")
        link = article.get("link", "")
        content = article.get("content", "")

        if link not in seen_articles:
            message_content = f"**Article Title:** {title}\n**Link:** {link}\n\n{content}"
            messages.append({"role": "system", "content": message_content})
            seen_articles.add(link)

    return 

def fetch_articles_from_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []

    # Locate article sections
    for article in soup.find_all('div', class_='grid-item item-s-9'):
        title_tag = article.find('h2', class_='font-cond font-size-large')
        link_tag = title_tag.find('a') if title_tag else None
        summary_tag = article.find_next_sibling('div', class_='grid-item font-mono font-color-grey')

        if title_tag and link_tag:
            title = title_tag.text.strip()
            link = link_tag['href']
            summary = summary_tag.text.strip() if summary_tag else 'No summary available'

            # Filter out unwanted guest author URLs and keep searching the correct ones
            if "guest_author" in link:
                correct_link = find_correct_link(article)
                if correct_link:
                    articles.append({'title': title, 'link': correct_link, 'summary': summary})
            else:
                articles.append({'title': title, 'link': link, 'summary': summary})

    return articles

def find_correct_link(article):
    # Attempt to find the correct link within the same article block
    for a_tag in article.find_all('a'):
        href = a_tag['href']
        if "guest_author" not in href:
            return href
    return None

# Function to find the next page link
def get_next_page(soup):
    next_page = soup.find('a', class_='next page-numbers')
    if next_page:
        return next_page['href']
    return None

# Function to fetch all articles from all pages
def fetch_all_articles(base_url):
    articles = []
    url = base_url

    while url:
        print(f"Fetching articles from: {url}")
        page_articles = fetch_articles_from_page(url)
        articles.extend(page_articles)

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        url = get_next_page(soup)  # Get the next page URL, if available

    return articles

def fetch_article_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return ""

    soup = BeautifulSoup(response.content, 'html.parser')

    content_div = soup.find('div', id='post-content')

    if not content_div:
        print("No 'post-content' div found.")
        return ""

    # Use a list to collect text content from paragraph tags
    content = []

    # Find all paragraph tags within the content div
    for element in content_div.find_all('p'):
        text = element.get_text(strip=True)
        if text:
            content.append(text)

    # Join the content into a single string with each piece of content separated by a newline
    full_content = '\n'.join(content)

    if not full_content:
        print("No content found in the 'post-content' div.")

    return full_content

# Function to save articles to a JSON file
def save_articles(articles, filename='articles.json'):
    # Check if the file already exists
    if os.path.exists(filename):
        # Open the file and load existing articles
        with open(filename, 'r') as f:
            existing_articles = json.load(f)
    else:
        existing_articles = []

    # Append new articles to the existing ones
    existing_articles.extend(articles)

    # Write the updated list of articles back to the file
    with open(filename, 'w') as f:
        json.dump(existing_articles, f, indent=4)

# Function to load articles from a JSON file
def load_articles(filename='articles.json'):
    with open(filename, 'r') as f:
        return json.load(f)


