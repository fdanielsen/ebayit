import quopri
import re
import urllib
import urlparse
from bs4 import BeautifulSoup

# TODO: Scan an IMAP inbox for eBay emails and get the HTML from those
htmlfile = open('testdata/emailpart.html', 'r')
html = htmlfile.read()
html = quopri.decodestring(html)

soup = BeautifulSoup(html)

item_links = soup.find_all('a', href=re.compile('ViewItem'))
url_re = re.compile('loc=([^&]+)')

# TODO: Only gather unique item URLs, currently finds some duplicates
item_description_urls = []
for item in item_links:
    url = url_re.search(item['href']).group(1)
    if url:
        url = urllib.unquote(url)
        parts = urlparse.urlparse(url)
        info = urlparse.parse_qs(parts.query)
        if 'item' in info:
            item_description_urls.append('http://vi.raptor.ebaydesc.com/ws/eBayISAPI.dll?ViewItemDescV4&item={0}'.format(info['item'][0]))



# NOTES:
# Sleeves measurement label might mention "shoulder", so might need to exclude
# that from the "sleeve" measurement search somehow...
measure_re = re.compile('(sleeves?|shoulders?|pit-to-pit|chest|waist|(?:\w+\s+)?length).{0,50}?(\d+(?:\.\d+)?)',
        re.IGNORECASE | re.DOTALL)

def parse_description(url):
    try:
        html = urllib.urlopen(url)
        # TODO: Remove <script> content
        description = BeautifulSoup(html)
        text = description.get_text()
        # TODO: Remove HTML comments here…
        result = measure_re.findall(text)
        print result

        # TODO: Filter results on measurement criteria
        # TODO: Alert throug email or similar for good finds
    except:
        pass

for url in item_description_urls:
    print url + ":\n\t"
    parse_description(url)
