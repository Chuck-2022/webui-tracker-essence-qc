import requests
import random
import os
from lxml import html
from datetime import datetime, timedelta, timezone
from time import gmtime, strftime

def get_time():
    toronto_offset_hours = -4  # adjust for daylight savings if needed
    toronto_tz = timezone(timedelta(hours=toronto_offset_hours))

    toronto_time = datetime.now(toronto_tz)
    return  toronto_time.strftime('%Y-%m-%d %H:%M:%S')

def fetch_data():
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
        'Referer': 'https://regieessencequebec.ca/',
    }

    secondes=[4,5,6,3,7,2,8,1,9]
    for s in secondes:
        minute = gmtime().tm_min - gmtime().tm_min%5
        url = f"https://regieessencequebec.ca/data/stations-{strftime('%Y%m%d%H', gmtime())}{minute:02d}{s:02d}.xlsx"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            break

    # Save the content to a file in binary mode
    path = "./data"
    if not os.path.exists(path):
        os.mkdir(path)
    with open(os.path.join(path,f"data.xlsx"), "wb") as f:
        f.write(response.content)

    return
