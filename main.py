from scripts.IVIndex import *
from scripts.NotionSearch import NotionSearch


notion_page_ids = []

n = NotionSearch(notion_page_ids, "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx")
scores = n.search("sample query")
print("scores", scores)
