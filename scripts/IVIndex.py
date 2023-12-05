import requests
import string
from collections import defaultdict
import re
import math
import sys

class IVIndex: 
    def __init__(self, page_ids, notion_secret, rich=False) -> None:
        self.page_ids = page_ids
        self.notion_secret = notion_secret
        self.notion_pages = self.get_notion_pages(page_ids)

        self.global_terms = []  # global terms 
        self.page_lengths = {} # page_id : page_length
        self.page_id_lexicon = self.construct_page_id_lexicon() 
        self.inverted_index = {}
        self.term_id_lexicon = {} 

        term_lex_counter = 0
        for notion_page_id, page_blocks in self.notion_pages.items():
            page_terms = self.retrieve_page_terms(page_blocks, rich, [])
            term_freqs = self.term_frequencies(page_terms)
            self.global_terms += page_terms
            for term in page_terms:
                if term in self.term_id_lexicon: # Term already in global lexicon, retreieve term id 
                    term_id = self.term_id_lexicon[term]
                else: # Assign new term_id to new term, save in term lexicon 
                    self.term_id_lexicon[term] = term_lex_counter
                    term_id = term_lex_counter
                    term_lex_counter += 1
                lex_page_id = self.page_id_lexicon[notion_page_id]
                if term_id in self.inverted_index: # Term_id already in inverted index, add page and term freq
                    self.inverted_index[term_id][lex_page_id] = term_freqs[term]
                else: # New term in inverted index, add page and term freq
                    term_pages = {lex_page_id: term_freqs[term]}
                    self.inverted_index[term_id] = term_pages
            self.page_lengths[notion_page_id] = len(page_terms)
        pass
            
    def __getitem__(self, term_id):
        return self.inverted_index[term_id]

    def retrieve_notion_page(self, page_id):
        """
        Makes an https request to notion api and retrieves all "blocks" in a page 

        Parameters:
            - page_id: a string representing the notion id of a notion page 
        Returns:
            - blocks: a list of json "blocks" that captures all text information in the page 
        """
        url = f'https://api.notion.com/v1/blocks/{page_id}/children'
        headers = {
            'Authorization': f'Bearer {self.notion_secret}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28',
        }
        payload = {}

        response = requests.get(url, headers=headers, json=payload)

        if response.status_code == 200:
            blocks = response.json()["results"]
            return blocks
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None

    def tokenize_word(self, word):
        """
        Tokenizes a word by removing spaces, making lower case, and removing punctuation 

        Parameters:
            - word: a string to be tokenized 
        Returns:
            - token: the tokenized word 
        """
        token = word.strip().lower().translate(str.maketrans('', '', string.punctuation + '“”'))
        return token 

    # rich parameter indicates whether to capture annotation and notion block type data
    def retrieve_page_terms(self, blocks, rich=False, terms=[]):
        """
        Recursively retrieves all terms in a list of notion blocks, including nested blocks 

        Parameters:
            - blocks: a list of ntion blocks representing a page, fetched from self.retrieve_notion_page
            - rich: a boolean indicating whether to capture rich text information (annotations and block type)
            - terms: a list of terms to be returned
        Returns:
            - terms: a list of terms in a given notion page 
        """
        for block in blocks:
            block_type = block["type"]
            block_content = block[block_type]
            has_children = bool(block["has_children"])
            if "rich_text" in block_content:
                text_content = block_content["rich_text"]
                for text in text_content:
                    raw_words = re.findall(r'\b\w+\b', text["plain_text"])

                    if rich:
                        # annotations is a set containing annotations applied to the text.
                        # It is empty if just regular plain text, options are the following:
                        # bold, italic, strikethrough, underlined, code
                        annotations = set(map(lambda x: x[0], filter(lambda x: (
                            x[0] != 'color') and x[1], text["annotations"].items())))

                        # type is the notion block type. e.g. text, heading1, callout, etc.
                        type = text['type']
                        for word in raw_words:
                            token = self.tokenize_word(word)
                            if token:
                                terms.append(((token, (type, annotations))))
                    else:
                        for word in raw_words:
                            token = self.tokenize_word(word)
                            if token:
                                terms.append((token))

            if has_children:
                block_id = block["id"]
                child_blocks = self.retrieve_notion_page(block_id)
                self.retrieve_page_terms(child_blocks, rich, terms)
        return terms


    def BM25_IDF_score(self, tf, avgdl, dl, n_t, N, k1, b):
        """
        Returns BM25 score for a term, and a Document
        
        Parameters:
            - tf: term frequency
            - avgdl: average document length
            - dl: document length
            - n_t: number of documents in corpus that contain term
            - N: total number of Documents in corpus
            - k1: tuning parameter
            - b: tuning parameter
        Returns:
            - doc_score: bm25 score for a particular document
        """

        term_frequency_component = tf * (k1 + 1) 
        IDF_component = math.log(((N - n_t + 0.5)/ (n_t + 0.5)) + 1)
        normalization_component = tf + k1 * (1 - b + (b *(dl/avgdl)))

        return IDF_component * (term_frequency_component / normalization_component)
    
    def construct_page_id_lexicon(self):
        """
        Constructs the page_id lexicon that maps a notion page id to an integer id 

        Returns:
            - lexicon: dict[notion_page_id] = integer id 
        """
        i = 0
        lexicon = {}
        for page_id in self.page_ids:
            if not page_id in lexicon:
                lexicon[page_id] = i
                i += 1
        return lexicon

    def construct_term_id_lexicon(terms):
        """
        Constructs the term_id lexicon that maps a notion term to an integer id 

        Returns:
            - lexicon: dict[term] = integer id 
        """
        i = 0
        lexicon = {}
        for term in terms:
            if not term in lexicon:
                lexicon[term] = i
                i += 1
        return lexicon
    
    def term_frequencies(self, terms):
        """
        Returns the frequency of each term in list of terms

        Parameters:
            - terms: a list of terms 
        Returns:
            - freqs: dict[term] = frequency of term

        """
        freqs = defaultdict(int)
        for term in terms:
            freqs[term] += 1
        return freqs

    def get_notion_pages(self, page_ids):
        """
        Gets notion pages as a dict of page blocks, page blocks are lists of strings

        Parameters:
            - page_ids: a list of notion page ids 
            - notion_secret: a notion api key
        Returns: 
            - pages: dict[page_id] = { page blocks[str] } 
        """
        pages = {}
        for page_id in page_ids:
            page_blocks = self.retrieve_notion_page(page_id)
            pages[page_id] = page_blocks

        return pages
