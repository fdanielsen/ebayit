#-*- coding: utf-8 -*-
from email.parser import Parser as EmailParser
import imaplib
import quopri
import re
import urllib
import urlparse
from bs4 import BeautifulSoup


try:
    import settings
except ImportError:
    import getpass
    settings = {
        'MAIL_HOST': 'localhost',
        'MAIL_USER': getpass.getuser(),
        'MAIL_PWD': getpass.getpass()
    }


# NOTES:
# Sleeves measurement label might mention "shoulder", so might need to exclude
# that from the "sleeve" measurement search somehow...
MEASURE_RE = re.compile('(sleeves?|shoulders?|pit-to-pit|chest|waist|(?:\w+\s+)?length).{0,50}?(\d+(?:\.\d+)?)',
        re.IGNORECASE | re.DOTALL)


def find_emails():
    """Connects to an IMAP inbox and searches for emails from eBay with new
    items from a saved search."""
    emails = []

    # Connect to the inbox
    mailbox = imaplib.IMAP4(settings.MAIL_HOST)
    mailbox.login(settings.MAIL_USER, settings.MAIL_PWD)
    mailbox.select('INBOX', readonly=True)

    # Search for emails from eBay with "New items" in the subject
    typ, data = mailbox.search(None,
            '(FROM "ebay@ebay")',
            '(SUBJECT "New items")')

    # Create a list of email message identifiers
    msgnums = data[0].split()
    # Create an RFC822 email parser
    parser = EmailParser()

    for num in msgnums:
        # Get the Unique IDentifier and complete message for each email
        typ, data = mailbox.fetch(num, '(UID RFC822)')

        meta = data[0][0].split()
        rfc822 = data[0][1]

        uid = meta[2]
        message = parser.parsestr(rfc822)

        # Find the HTML part of the message
        for part in message.walk():
            if part.get_content_type() == 'text/html':
                emails.append({
                    'UID': uid,
                    'HTML': part.get_payload(decode=True)
                })
    return emails


def parse_html(html):
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
    return item_description_urls


def parse_description(url):
    result = None
    try:
        html = urllib.urlopen(url)

        # TODO: Remove <script> content
        description = BeautifulSoup(html)
        text = description.get_text()

        # TODO: Remove HTML comments here…
        result = MEASURE_RE.findall(text)
    except:
        pass
    return result


for email in find_emails():
    for url in parse_html(email['HTML']):
        print url + ":\n\t"
        result = parse_description(url)

        # TODO: Filter results on measurement criteria
        # TODO: Alert throug email or similar for good finds
        print result
