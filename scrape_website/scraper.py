import time
from urllib.parse import urlparse, urljoin

import html2text
import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from googlesearch import search
from readability import Document
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from scrape_website.settings import cwd

root_endpoint = None
chromedriver = ChromeDriverManager().install()
global_driver = None


def read_sitemap(sitemap_url):
    site_urls = []

    r = requests.get(sitemap_url)
    xml = r.text

    soup = BeautifulSoup(xml, "lxml")
    sitemap_tags = soup.find_all("loc")

    for location in sitemap_tags:
        site_urls.append(location.text)
    return site_urls


def get_stealth_chromedriver():
    options = uc.ChromeOptions()
    # options.headless = True
    # options.add_argument('--headless')
    options.user_data_dir = cwd + "/profile"
    return uc.Chrome(options=options, version_main=111)


def set_cookies_from_page(driver, url):
    response = requests.get(url)
    if response.status_code == 200:
        cookies = response.cookies.get_dict()
        driver.add_cookie(cookies)


def get_user_agent():
    # return "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 OPR/97.0.0.0"


def set_request_headers(driver):
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 OPR/97.0.0.0"
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})
    # driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": {
    #     'origin': 'https://wellfound.com',
    #     'referer': 'https://wellfound.com/',
    #     'sec-ch-ua': '"Not?A_Brand";v="99", "Opera";v="97", "Chromium";v="111"',
    #     'sec-ch-ua-mobile': '?0',
    #     'sec-ch-ua-platform': '\"macOS\"',
    #     'sec-fetch-dest': 'empty',
    #     'sec-fetch-mode': 'cors',
    #     'sec-fetch-site': 'same-site',
    #     'authority': 'wellfound.com'
    # }})


def get_cached_url(url):
    return f"https://webcache.googleusercontent.com/search?q=cache:{url}&cd=3&hl=en&ct=clnk&gl=in"


def get_search_urls(query, base_url, num_results=10, start=0):
    urls = []
    search_results = search(query, start=start, num=num_results, user_agent=get_user_agent())
    for url in search_results:
        if base_url in url:
            urls.append(url)
    return urls


def scroll(driver):
    start = time.time()

    # will be used in the while loop
    initialScroll = 0
    finalScroll = 1000

    while True:
        driver.execute_script(f"window.scrollTo({initialScroll},{finalScroll})")
        initialScroll = finalScroll
        finalScroll += 1000

        time.sleep(1)

        end = time.time()

        if round(end - start) > 6:
            break

    return


def create_driver_object():
    global global_driver
    options = Options()
    # options.headless = True
    options.add_argument('--headless')
    options.user_data_dir = cwd + "/profile"
    # options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    # options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    prefs = {
        "profile.default_content_setting_values": {
            "images": 2,
            "javascript": 1  # Disable JavaScript if not needed
        }
    }
    options.add_experimental_option("prefs", prefs)
    # options.page_load_strategy = 'eager'
    # driver = webdriver.Chrome(options=options)
    global_driver = webdriver.Chrome(options=options)
    global_driver.maximize_window()
    set_request_headers(global_driver)
    return global_driver


def get_html_content_using_selenium(url):
    # driver = webdriver.Chrome(options=options)
    global global_driver
    if global_driver is None:
        global_driver = create_driver_object()
    global_driver.get(url)
    page_source = global_driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    body = soup.find("body")
    body_content = body.text

    return soup, body, body_content, page_source


def get_html_content(url, extract_raw=False):
    # driver.get(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    body = soup.find("body")
    # print(body.text)
    if extract_raw:
        return soup, body, body.text, response.content
    return body


def get_links(url, html_content):
    if not html_content:
        return []

    base_url = urlparse(url).scheme + '://' + urlparse(url).hostname
    links = [urljoin(base_url, link.get('href').strip()) for link in html_content.find_all('a', href=True)]
    ids_to_remove = []
    for idx, link in enumerate(links):
        if root_endpoint not in link:
            ids_to_remove.append(idx)

    count = 0
    for idx in ids_to_remove:
        del links[idx - count]
        count += 1

    return links


def get_formatted_text(element):
    if element.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return ''
    if isinstance(element, str):
        return element
    formatted_text = ''
    for child in element.children:
        formatted_text += get_formatted_text(child)
    return formatted_text.strip()


def extract_main_text_content_w_formatting(url, html_content, cur_url):
    global root_endpoint
    root_endpoint = url
    intro = html_content.find_all('div')
    data_web = []
    add_more = ''
    for k in range(len(intro)):
        ask = 0
        if k != len(intro) - 1:
            if intro[k].get_text() in intro[k + 1].get_text():
                continue
            if len(intro[k].find_all('div')) > 0:
                if len(intro[k].get_text()) > 1000:
                    continue

        p0 = html2text.html2text(str(intro[k]))
        p1 = p0.replace("#", "").replace("*", "").replace("[", "").replace("]", "").replace("()", "")
        p2 = ""
        p3 = ""
        skip = False
        for i in range(len(p1)):
            try:
                if (skip == True):
                    if p1[i] == ")":
                        skip = False
                    continue
                if p1[i] == "!" or p1[i] + p1[i + 1] == "(/":
                    skip = True
                    continue
                else:
                    p2 += p1[i]
            except:
                p2 += p1[i]
        lines = p2.splitlines()
        if len(lines) > 1:
            for l in lines:
                if (l == ""):
                    continue
                p3 += l.strip() + "\n"
        else:
            p3 = p2
        for data in data_web:
            if p3 in data:
                ask = 1
        if ask == 1:
            continue
        links = get_links(cur_url, intro[k])
        if len(links):
            p3 += "For more reading : "
            for m in links:
                if m not in p3:
                    p3 += "\n" + m

        if len(intro[k]) < 30 and len(intro[k].find_all('div')) == 0:
            add_more = p3
            continue

        if add_more != '':
            p3 = add_more + p3
            add_more = ''

        data_web.append(p3)
    return data_web


def extract_main_text_content_raw(html_content):
    document = Document(html_content)
    content_html = document.summary()
    content_markdown = html2text.html2text(content_html)
    return content_markdown


def extract_main_text_content_raw_content(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    intro = soup.find('body')
    intro_text = intro.get_text()
    print("intro : ", intro_text)
    header = intro.find('div', {'class': 'header'})
    footer = intro.find('div', {'class': 'footer'})
    if (header != None):
        intro_text = intro_text.replace(header.get_text(), "")
    if (footer != None):
        intro_text = intro_text.replace(footer.get_text(), "")
    return intro_text


def main():
    url = input("Enter the URL of the web page you'd like to extract main text content from: ")
    body_code = get_html_content(url, create_driver_object())
    main_text_content = extract_main_text_content_w_formatting(body_code)

    print("\nMain Text Content (HTML format):")
    print(main_text_content)


# read_sitemap("https://drmalpani.com/sitemap.xml")

# if __name__ == "__main__":
#     main()
