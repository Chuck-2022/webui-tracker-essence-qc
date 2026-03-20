import requests
import random 
from lxml import html
from datetime import datetime, timedelta, timezone

def get_time():
    toronto_offset_hours = -4  # adjust for daylight savings if needed
    toronto_tz = timezone(timedelta(hours=toronto_offset_hours))

    toronto_time = datetime.now(toronto_tz)
    return  toronto_time.strftime('%Y-%m-%d %H:%M:%S')

def lint_data(data):
    try:
        return data.encode('latin1').decode('utf-8')
    except:
        return data
    

def fetch_data(url):
    # Test if URL is accessible
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    t = random.choice(USER_AGENTS)
    headers = {
        'User-Agent': t,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.gasbuddy.com/',
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    response.encoding = 'utf-8'
    
    # Scrape data
    tree = html.fromstring(response.content)
    
    # Extract name
    name_xpath = "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h1"
    name_elements = tree.xpath(name_xpath)
    name_data = name_elements[0].text.strip() if name_elements else "Unknown"
    name_data = lint_data(name_data)
    # Extract price
    price_xpath = "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[1]/div[1]/div[3]/div/div[2]/div[2]/div[1]/span"
    price_elements = tree.xpath(price_xpath)
    price_data = price_elements[0].text.strip() if price_elements else "N/A"
    price_data = price_data.replace('Â', '').replace('¢', '¢').strip()

    # Extract last updated
    updated_xpath = "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[1]/div[1]/div[3]/div/div[2]/div[2]/div[1]/div/p"
    updated_elements = tree.xpath(updated_xpath)
    updated_data = updated_elements[0].text.strip() if updated_elements else "Unknown"

    # Extract gmap link
    try:
        address_xpath1 = "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div/span/span[1]"
        address_elements1 = tree.xpath(address_xpath1)[0]
        address_xpath2 = "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div/span/span[3]/br"
        address_elements2 = tree.xpath(address_xpath2)[0]
        address_data = address_elements1.text.strip() + address_elements2.tail.strip()
        address_data = lint_data(address_data)
    except:
        try:
            address_xpath1 = "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[3]/div/span/span[1]"
            address_elements1 = tree.xpath(address_xpath1)[0]
            address_xpath2 = "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[3]/div/span/span[3]/br"
            address_elements2 = tree.xpath(address_xpath2)[0]
            address_data = address_elements1.text.strip() + address_elements2.tail.strip()
            address_data = lint_data(address_data)
        except:
            address_data = ''
            address_data = ''

    gmap_base = "https://www.google.com/maps/dir//"
    address = address_data.replace(' ',"+")
    gmap_link = gmap_base + address
    return name_data, price_data, updated_data, gmap_link
