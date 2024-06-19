from advanced_crawler import scrape_website, scrape_website_using_sitemap
from settings import ScraperParams as SP

scrape_website_using_sitemap(SP.URL, SP.sitemap_url, SP.namespace)

# scrape_website(SP.URL, SP.max_depth, SP.max_webpages, SP.namespace, SP.pinecone_index, only_scrape=True)
