from scripts.IVIndex import *
from scripts.NotionSearch import NotionSearch


# Add your notion page URLs to this list
notion_page_urls = []

# Add your secret key here 
n = NotionSearch(notion_page_urls,
                 "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
n.cli_search()
