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
        url = f'https://api.notion.com/v1/blocks/{page_id}/children'
        headers = {
            'Authorization': f'Bearer {self.notion_secret}',
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

    def tokenize_word(self, word):
        # Removes spaces, makes lower case, removes punctuation
        # Added "“”" because for some reason that doesnt count as puncutation
        return word.strip().lower().translate(str.maketrans('', '', string.punctuation + '“”'))

    # rich parameter indicates whether to capture annotation and notion block type data
    def retrieve_page_terms(self, blocks, rich=False, terms=[]):
        for block in blocks:
            block_type = block["type"]
            block_content = block[block_type]
            has_children = bool(block["has_children"])
            if "rich_text" in block_content:
                text_content = block_content["rich_text"]
                for text in text_content:
                    # tokenized_words is the list of terms in the block
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
        i = 0
        lexicon = {}
        for page_id in self.page_ids:
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
    
    def term_frequencies(self, terms):
        freqs = defaultdict(int)
        for term in terms:
            freqs[term] += 1
        return freqs
    
    # Parameters:
    # #    - notion_pages: a dict[page_id] = { page blocks[str] }
    # # Returns:
    # #    - tuples: a list of tuples represting the inverted index ([term_id, page_id, term_frequency])
    # #    - term_id_lexicon: the term id lexicon that maps terms to integers
    # #    - page_id_lexicon: the page id lexicon that maps page_ids to integers
    # def construct_inverse_index_tuples(self, notion_pages: dict):
    #     page_id_lexicon = construct_page_id_lexicon()
    #     global_terms = []
    #     tuples = []
    #     for page_id, page_blocks in notion_pages.items():
    #         page_terms = self.retrieve_page_terms(page_blocks)
    #         for term in page_terms:
    #             tuples.append([term, page_id_lexicon[page_id], term_freqs[term]])
    #         global_terms += page_terms
    #     term_id_lexicon = construct_term_id_lexicon(global_terms)
    #     for tuple in tuples:
    #         tuple[0] = term_id_lexicon[tuple[0]]
    #     tuples.sort(key=lambda x: x[0])
    #     return tuples, term_id_lexicon, page_id_lexicon


    # def get_inverted_index(self, tuples):
    #     """
    #     Parameters:
    #         - tuples: a list of tuples represting the inverted index ([term_id, page_id, term_frequency])
    #     Returns:
    #         - inverted_index: a 2 layer deep dict represting the inverted index [term_id][page_id][term_frequency]
    #     """
    #     inverted_index = {}

    #     for tuple in tuples:
    #         term_id, page_id, term_frequencies = tuple

    #         term_pages = inverted_index.get(term_id, {})

    #         if page_id in term_pages.keys():
    #             if term_pages[page_id] != term_frequencies:
    #                 print('inverted index was contructed incorrectly')
    #                 sys.exit(1)

    #         term_pages[page_id] = term_frequencies

    #         inverted_index[term_id] = term_pages
    
    #     return inverted_index




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
