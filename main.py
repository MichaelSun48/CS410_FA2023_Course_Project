from scripts.IVIndex import *
from scripts.NotionSearch import NotionSearch



notion_page_urls = []

n = NotionSearch(notion_page_urls,
                 "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
n.cli_search()
# scores = n.search("sample query")
# print("scores", scores)
