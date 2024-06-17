import csv
import sys
import traceback
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

import insert_raw_sheet
from scraper import extract_main_text_content_w_formatting, extract_main_text_content_raw, \
    get_html_content_using_selenium

maxInt = sys.maxsize

root_endpoint = None
max_webpages = 10
driver = None
context_id = 0
count = 1
webpage_count = 1

filename = "temp.csv"

website_data = []


# Function to save data to CSV
def save_to_csv(data):
    with open(filename, 'a+', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data.keys())

        # Write header only if file is empty
        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow(data)


def normalize_url(url):
    # Normalize the URL by removing trailing slashes and fragments
    _parsed_url = urlparse(url)
    return _parsed_url._replace(path=_parsed_url.path.rstrip('/'), fragment='', query='').geturl()


def get_html_content_requests(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
        return html_content
    except requests.RequestException:
        print(f"Failed to fetch the content for {url}. Skipping this URL.")
        return None


def get_links(url, html_content):
    if not html_content:
        return []
    if isinstance(html_content, str):
        soup = BeautifulSoup(html_content, 'html.parser')
    else:
        soup = html_content
    base_url = urlparse(url).scheme + '://' + urlparse(url).hostname
    links = [urljoin(base_url, link.get('href').strip()) for link in soup.find_all('a', href=True)]
    ids_to_remove = []
    for idx, link in enumerate(links):
        if root_endpoint not in link:
            ids_to_remove.append(idx)

    count = 0
    for idx in ids_to_remove:
        del links[idx - count]
        count += 1

    return links


def is_allowed(url, rp):
    if not rp:
        return True
    return rp.can_fetch("*", url)


def crawl_website(url, max_depth=3, current_depth=1, visited=None, robots_txt_url=None, rp=None):
    global context_id, count, webpage_count, website_data
    try:
        url = normalize_url(url)
    except:
        pass

    if webpage_count >= max_webpages:
        return

    if visited is None:
        visited = set()

    if current_depth > max_depth:
        return

    if url in visited:
        return

    for idx, x in enumerate(website_data):
        if url == x["url"]:
            visited.add(url)
            webpage_count += 1
            context_id += 1
            links = get_links(x["url"], x["html_code"])
            del website_data[idx]
            for link in links:
                crawl_website(link, max_depth, current_depth + 1, visited, robots_txt_url, rp)
            return

    visited.add(url)
    webpage_count += 1
    if not is_allowed(url, rp):
        print(f"URL not allowed by robots.txt: {url}")
        return

    try:
        # html_content = HTML code of body tag.
        # raw_html_content = All Text inside body tag
        # readable_raw_content = Entire HTML code
        # html_code, body_code, raw_html_content, readable_raw_content = get_html_content(url, True)
        soup_object, body_code, raw_html_content, html_code = get_html_content_using_selenium(url)
        # readable_content = Readable content of the webpage (May skip most of the page content)
        readable_content = extract_main_text_content_raw(html_code)
        # Array of website content fetched using a complex logic.
        main_text_content = extract_main_text_content_w_formatting(root_endpoint, body_code, url)
        main_text_content_combined = ""
        for k in main_text_content:
            main_text_content_combined += k.strip() + "\n---x---\n"
        print("URL confirmed: ", url)
        save_to_csv(
            {"url": url, "context_id": context_id, "content": main_text_content_combined, "html_code": html_code,
             "raw_html_content": raw_html_content, "readable_content": readable_content, "depth": current_depth})

        context_id += 1

        links = get_links(url, soup_object)
        for link in links:
            crawl_website(link, max_depth, current_depth + 1, visited, robots_txt_url, rp)
    except Exception as e:
        print("ERROR at url:", url)
        traceback.print_exc()


def get_robots_txt_parser(robots_txt_url):
    rp = RobotFileParser()
    try:
        rp.set_url(robots_txt_url)
        rp.read()
        return rp
    except Exception as e:
        print(f"Failed to fetch robots.txt from {robots_txt_url}. Continuing without robots.txt rules.")
        return None


def read_csv_to_list_of_dicts(file_path):
    try:
        with open(file_path, mode='r', newline='') as file:
            pass
    except:
        return []
    global maxInt
    while True:
        # decrease the maxInt value by factor 10
        # as long as the OverflowError occurs.

        try:
            csv.field_size_limit(maxInt)
            break
        except OverflowError:
            maxInt = int(maxInt / 10)
    data = []
    with open(file_path, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data


def scrape_website(url, max_depth, num_pages, output_csv, pinecone_index, only_scrape=False):
    global max_webpages, root_endpoint, driver, context_id, filename, website_data

    filename = output_csv + "_raw.csv"
    # driver = create_driver_object()

    website_data = read_csv_to_list_of_dicts(filename)

    max_webpages = num_pages
    root_endpoint = url

    parsed_url = urlparse(url)
    robots_txt_url = urljoin(f"{parsed_url.scheme}://{parsed_url.hostname}", "robots.txt")
    rp = get_robots_txt_parser(robots_txt_url)
    crawl_website(url, max_depth, visited=set(), robots_txt_url=robots_txt_url, rp=rp)

    if only_scrape:
        return

    # count = 1
    # descriptions = []
    # for row in website_data:
    #     add = []
    #     add.append(row['content'])
    #     add.append(row['context_id'])
    #     add.append(row['url'])
    #     count += 1
    #     descriptions.append(add)
    #
    # insert_raw_sheet.insert_raw_data(descriptions, output_csv, pinecone_index)


def process_from_file(output_csv, pinecone_index, input_csv="apnipathshala_processed.csv"):
    website_data = read_csv_to_list_of_dicts(input_csv)

    count = 1
    descriptions = []
    for row in website_data:
        if len(row["content"]) < 50:
            continue
        add = []
        add.append(row['content'])
        add.append(row['context_id'])
        add.append(row['url'])
        count += 1
        descriptions.append(add)

    insert_raw_sheet.insert_raw_data(descriptions, output_csv, pinecone_index)
