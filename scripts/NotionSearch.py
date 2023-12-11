import re
import string
from scripts.IVIndex import *
from statistics import mean


class NotionSearch:
    def __init__(self, page_urls, notion_integration_secret, rich=False) -> None:
        self.page_urls_map = self._map_notion_url_id(page_urls)
        self.page_ids = self.page_urls_map.keys()
        print("building inverted index...")
        self.inverted_index = IVIndex(
            self.page_ids, notion_integration_secret, rich)
        self.page_id_lexicon = self.inverted_index.page_id_lexicon
        self.term_id_lexicon = self.inverted_index.term_id_lexicon
        self.page_lengths = self.inverted_index.page_lengths
        self.pageId_url_map = self.inverted_index.pageId_url_map

        self.avg_page_length = mean(self.page_lengths.values())

        self.num_documents = len(self.page_id_lexicon)

    def _map_notion_url_id(self, page_urls):
        page_ids = {}
        for url in page_urls:
            # Find all matches of a 32-digit hexadecimal string
            matches = re.findall(r'[a-fA-F0-9]{32}', url)
            if matches:
                # Assuming the first match is the page ID
                page_ids[matches[0]] = url
        return page_ids

    def _print_page(self, page_id):
        words = []

        for block in self.notion_pages[page_id]:
            block_type = block["type"]
            block_content = block[block_type]
            if "rich_text" in block_content:
                text_content = block_content["rich_text"]
                for text in text_content:
                    # tokenized_words is the list of terms in the block
                    raw_words = re.findall(r'\b\w+\b', text["plain_text"])
                    for word in raw_words:
                        token = IVIndex.tokenize_word(word)
                        if token:
                            words.append(token)
        return words

    def search(self, query: str):
        query_tokens = []
        # raw_words = filter(lambda x: len(x) > 0, query.split(' '))
        raw_words = re.findall(r'\b\w+\b', query)

        for word in raw_words:
            token = self.inverted_index.tokenize_word(word)
            query_tokens.append(token)

        query_term_ids = [self.term_id_lexicon.get(
            token, None) for token in query_tokens]

        scored_query = self.query_page_scores(query_term_ids)

        sorted_page_scores = sorted(
            scored_query.items(), key=lambda x: x[1], reverse=True)

        return sorted_page_scores

    def cli_search(self,):
        print(" _   _         _    _                 ____                            _     \n| \\ | |  ___  | |_ (_)  ___   _ __   / ___|   ___   __ _  _ __   ___ | |__  \n|  \\| | / _ \\ | __|| | / _ \\ | '_ \\  \\___ \\  / _ \\ / _` || '__| / __|| '_ \\ \n| |\\  || (_) || |_ | || (_) || | | |  ___) ||  __/| (_| || |   | (__ | | | |\n|_| \\_| \\___/  \\__||_| \\___/ |_| |_| |____/  \\___| \\__,_||_|    \\___||_| |_|\n                                                                            ")
        while True:
            print('\n\nEnter Query:')
            query = input()
            search_results = self.search(query)

            print('\n\n Search Results:\n')

            for index, (page_id, score) in enumerate(search_results):
                print(f"{index + 1}. score: {score} url: {self.pageId_url_map[page_id]} \n")

    def query_page_scores(self, query_term_ids):
        """
        Given dict of page_ids -> page blocks, and a tokenized query return the ranking of page_ids

        Parameters:
            - query: list of ids's corrosponding to term ids 
            - pages: dict of page_ids -> page_blocks
        Returns:
            - ranked_list: ranked list of page ids
        """

        page_scores = {}

        for page_id in self.page_ids:

            page_score = 0.0
            for token_id in query_term_ids:
                if token_id:  # None means that token doesn't exist in corpus
                    page_id_int = self.page_id_lexicon[page_id]

                    tf = self.inverted_index[token_id].get(page_id_int, 0)

                    n_t = len(self.inverted_index[token_id])

                    page_score += self.inverted_index.BM25_IDF_score(
                        tf, self.avg_page_length, self.page_lengths[page_id], n_t, self.num_documents, k1=1.2, b=0.75)

            page_scores[page_id] = page_score

        return page_scores
        # rank pages

    def get_page_lengths(self,):
        return IVIndex.get_page_lengths(self.notion_pages)
