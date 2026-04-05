import requests
from time import gmtime, strftime
import random
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

seconde=0
while True:
    minute = gmtime().tm_min - gmtime().tm_min%5
    url = f"https://regieessencequebec.ca/data/stations-{strftime('%Y%m%d%H', gmtime())}{minute:02d}{seconde:02d}.xlsx"
    print(url)
    print("https://regieessencequebec.ca/data/stations-20260403031505.xlsx")
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        break
    else:
        seconde+=1
print('ok')