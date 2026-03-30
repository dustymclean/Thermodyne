import requests
from bs4 import BeautifulSoup
html = requests.get('https://thermodynesystems.com/wholesaler/us/vapes.html').text
soup = BeautifulSoup(html, 'html.parser')
p = soup.select_one('li.item.product')
if p:
    print(p.prettify()[:1500])
