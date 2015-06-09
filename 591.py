import urllib2
import json

__author__ = 'warenix'

def fetch_page(page_no):
    TYPE_RENT = 1
    TYPE_BUY = 2

    REGION_HONGKONG = 1
    REGION_KOWLOON = 2
    REGION_NT = 3
    url = 'http://rent.591.com.hk/?m=home&c=search&a=rslist&type={type}&p={page_no}&searchtype=1&purpose=1&region={region}'.format(
        page_no = page_no,
        type=TYPE_RENT,
        region=REGION_HONGKONG
    )

    cookie = 'think_language=zh-hk; PHPSESSID=2v8oj7b93vqk2l3p5noaebfln3; think_template=default'
    headers = {
        'Cookie':cookie,
        'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0',
        'Referer': 'http://rent.591.com.hk/?aid=4&gclid=CMGxuqy2-8UCFVKUfgodFTcAjQ',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
    }
    request = urllib2.Request(url, headers=headers)
    html = urllib2.urlopen(request).read()
    #print html
    j = json.loads(html)
    for item in j['items']:
        # for k in item:
        #     print k, ":", item[k]
        # print item
        print_item_rent(item)

class Item(object):
    name = None

    def set_name(self, name):
        self.name = name
        return self

def print_item_rent(item, delimiter='\t'):
    s = ''
    s += item['area'].strip()
    s += delimiter
    s += item['district'].strip()
    s += delimiter
    s += item['community'].strip()
    s += delimiter
    s += item['address'].strip()
    s += delimiter
    s += item['floor'][:-1]
    s += delimiter
    s += item['room'] + item['search_rooms_str'] + item['hall'] + item['search_halls_str']
    s += delimiter
    s += item['use_area_str'] + '/' + item['build_area_str']
    s += delimiter
    s += item['price_str']
    s += delimiter
    s += item['room']
    s += delimiter
    s += item['hall']
    s += delimiter
    s += item['age']
    s += delimiter
    s += item['use_area_str'][:-1]
    s += delimiter
    s += item['build_area_str'][:-1]
    s += delimiter
    s += item['price_str'].replace(',', '')[:-1]
    s += delimiter
    s += item['detailUrl']
    s += delimiter
    s += item['post_id']
    s += delimiter
    s += item['ltime']
    s += delimiter
    s+= item['refreshtime']
    s += delimiter
    if s != '':
        print s.encode('utf-8', 'ignore')

for i in range(1,100):
    fetch_page(i)

