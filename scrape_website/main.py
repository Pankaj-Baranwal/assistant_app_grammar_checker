from advanced_crawler import scrape_website
from settings import ScraperParams as SP

scrape_website(SP.URL, SP.max_depth, SP.max_webpages, SP.namespace, SP.pinecone_index, only_scrape=True)
