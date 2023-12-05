import re
import scripts.IVIndex as IVIndex
import string
from statistics import mean


class NotionSearch:
    def __init__(self, page_ids, notion_integration_secret) -> None:
        self.page_ids = page_ids
        self.notion_pages = IVIndex.get_notion_pages(
            page_ids, notion_integration_secret)
        
        self.tuples, self.term_id_lexicon, self.page_id_lexicon = IVIndex.construct_inverse_index_tuples(
            self.notion_pages)
        
        self.inverted_index = IVIndex.get_inverted_index(self.tuples)

        self.page_lengths = IVIndex.get_page_lengths(self.notion_pages)

        self.avg_page_length = mean(self.page_lengths.values())

        self.num_documents = len(self.page_id_lexicon)

        pass

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
            token = IVIndex.tokenize_word(word)
            query_tokens.append(token)

        query_term_ids = [self.term_id_lexicon.get(
            token, None) for token in query_tokens]
        

        return self.rank_query(query_term_ids)

    def rank_query(self, query_term_ids):
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
                if token_id: # None means that token doesn't exist in corpus
                    page_id_int = self.page_id_lexicon[page_id]



                    tf = self.inverted_index[token_id].get(page_id_int,0)

                    


                    n_t = len(self.inverted_index[token_id])

                    page_score += IVIndex.BM25(tf, self.avg_page_length,
                                self.page_lengths[page_id], n_t, self.num_documents, k1=1.2, b=0.75)

            page_scores[page_id] = page_score

        return page_scores
        # rank pages
    def get_page_lengths(self,):
        return IVIndex.get_page_lengths(self.notion_pages)
