import json
import time
import urllib
import urllib2

import re

from renthse.core.db import HousingDB, House, SOURCE_TYPE_HSE28

__author__ = 'warenix'


class ParserHse28(object):
    __db = None
    __row_count = 0
    __cj = None
    __opener = None

    __cookie = None
    __session_id = None

    __page_no = 1

    def __init__(self, page_no=None):
        self.__db = HousingDB()
        self.__db.init_db()

        if page_no is not None:
            self.__page_no = page_no

    def fetch_page(self):
        url = "http://m.28hse.com/tc/webservice"
        while True:
            data = urllib.urlencode({'s_order': 0,
                                     's_order_direction': 10,
                                     's_sellrent': 2,
                                     'district_select_multiple': 'g10',
                                     's_source': 0,
                                     's_type': 'g1',
                                     'stype1': "g1",
                                     's_rent': 0,
                                     's_area': 0,
                                     's_area_buildact': 2,
                                     's_keywords': '',
                                     's_page': self.__page_no,
                                     'cmd': 'listings',
                                     })
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Content-Length': len(data),
                # 'Referer': 'http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/?mktid=HK&minprice=&maxprice=&minarea=&maxarea=&areatype=N&posttype=S&src=F',
                'X-Requested-With': 'XMLHttpRequest'}

            print 'fetching', self.__page_no, url
            print data
            print
            request = urllib2.Request(url, headers=headers, data=data)
            response = urllib2.urlopen(request)
            headers = response.info()
            html = response.read()
            response.close()

            if html is not "":
                j = json.loads(html)
                if not self.process_page(j['posts']):
                    break
            self.__page_no += 1

    def process_page(self, posts):
        if len(posts) == 0:
            return False

        pattern_usable = u"\u5be6\u7528(\d+)"
        pattern_room = u"(\d+)\u623f"
        pattern_rent = u"\u79df (\d+,?\d+)"
        print pattern_usable

        row_count = 0
        for item in posts:
            print item
            print item['catfathername']  # district
            print item['second_sent']
            # print item['ad_description']
            # print item['ad_title']
            print item['rentprice']
            print item['catname']
            print item['first_sent']

            source_id = item['ad_id']
            room = None
            use_area = None
            rent = None
            matcher1 = re.search(pattern_usable, item['second_sent'])
            if matcher1:
                use_area = matcher1.group(1)
            matcher1 = re.search(pattern_room, item['second_sent'])
            if matcher1:
                room = matcher1.group(1)
            matcher1 = re.search(pattern_rent, item['rentprice'])
            if matcher1:
                rent = matcher1.group(1).replace(',', '')
            print

            d = {
                'source_type': SOURCE_TYPE_HSE28,
                'source_id': source_id,
                'area': item['area'].strip(),
                'district': None,
                'community': item['catfathername'].strip(),
                'address': item['first_sent'].strip().split()[1],
                'floor': None,
                'room': room,
                'hall': None,
                'age': None,
                'use_area': use_area,
                'build_area': None,
                'price': rent,
                'source_url': "http://www.28hse.com/rent-property-%s.html" % (source_id),
                'refresh_time': time.time(),
            }

            print d

            house = House(SOURCE_TYPE_HSE28)
            house.upsert(self.__db, d)
            if row_count < 20:
                row_count += 1
            else:
                row_count = 0
                self.__db.con.commit()

        if row_count > 0:
            self.__db.con.commit()
            pass

        return True


if __name__ == '__main__':
    parser = ParserHse28()
    for i in range(1, 300):
        parser.fetch_page(i)
