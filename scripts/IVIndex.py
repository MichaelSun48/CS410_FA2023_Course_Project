import requests 
import string 
from collections import defaultdict


def retrieve_notion_page(page_id, notion_token):
    url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    headers = {
        'Authorization': f'Bearer {notion_token}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28',  
    }
    payload = {}

    response = requests.get(url, headers=headers, json=payload) 

    if response.status_code == 200:
        data = response.json()["results"]
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    

def tokenize_word(word):
    # Removes spaces, makes lower case, removes punctuation 
    # Added "“”" because for some reason that doesnt count as puncutation 
    return word.strip().lower().translate(str.maketrans('', '', string.punctuation + '“”'))


# rich parameter indicates whether to capture annotation and notion block type data
def retrieve_page_terms(blocks, rich=False):
    terms = []
    for block in blocks:
        block_type = block["type"]
        block_content = block[block_type]
        if "rich_text" in block_content:
            text_content = block_content["rich_text"]
            for text in text_content:
                # tokenized_words is the list of terms in the block 
                raw_words = filter(lambda x: len(x) > 0, text["plain_text"].split(' '))
                
                if rich:
                    # annotations is a set containing annotations applied to the text. 
                    # It is empty if just regular plain text, options are the following:
                    # bold, italic, strikethrough, underlined, code
                    annotations = set(map(lambda x: x[0], filter(lambda x: (x[0] != 'color') and x[1], text["annotations"].items())))
                    
                    # type is the notion block type. e.g. text, heading1, callout, etc.
                    type = text['type']
                    for word in raw_words:
                        token = tokenize_word(word)
                        if token:
                            terms.append(((token, (type, annotations))))
                else:
                    for word in raw_words:
                        token = tokenize_word(word)
                        if token:
                            terms.append((token))
    return terms

def construct_page_id_lexicon(page_ids):
    i = 0
    lexicon = {}
    for page_id in page_ids:
        if not page_id in lexicon:
            lexicon[page_id] = i
            i += 1
    return lexicon

def construct_term_id_lexicon(terms):
    i = 0
    lexicon = {}
    for term in terms:
        if not term in lexicon:
            lexicon[term] = i
            i += 1
    return lexicon

def term_frequencies(terms):
    freqs = defaultdict(int)
    for term in terms:
        freqs[term] += 1 
    return freqs 

# Parameters:
#    - page_ids: a list of notion page ids 
#    - notion_secret: a notion api key
# Returns:
#    - tuples: a list of tuples represting the inverted index ([term_id, page_id, term_frequency])
#    - term_id_lexicon: the term id lexicon that maps terms to integers
#    - page_id_lexicon: the page id lexicon that maps page_ids to integers
def construct_inverse_index(page_ids, notion_secret):
    page_id_lexicon = construct_page_id_lexicon(page_ids)
    global_terms = [] 
    tuples = []
    for page_id in page_ids:
        page_blocks = retrieve_notion_page(page_id, notion_secret)
        page_terms = retrieve_page_terms(page_blocks)
        term_freqs = term_frequencies(page_terms)
        for term in page_terms:
            tuples.append([term, page_id_lexicon[page_id], term_freqs[term]])
        global_terms += page_terms
    term_id_lexicon = construct_term_id_lexicon(global_terms)
    for tuple in tuples:
        tuple[0] = term_id_lexicon[tuple[0]]
    tuples.sort(key=lambda x: x[0])
    return tuples, term_id_lexicon, page_id_lexicon
                

