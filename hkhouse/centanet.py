import json
import urllib
import urllib2
import re
import time
from hkhouse.db import HousingDB, House, SOURCE_TYPE_CENTANET
from hkhouse.htmlparser import BaseParser

__author__ = 'warenix'


class ParserCentanet(object):
    __db = None
    __row_count = 0
    __cj = None
    __opener = None

    __cookie = None
    __session_id = None

    def __init__(self):
        self.__db = HousingDB()
        self.__db.init_db()

    def fetch_page(self, page_no):
        url = "http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/?"
        f = {'mktid': 'HK',
             'minprice': '',
             'maxprice': '', 'minarea': '', 'maxarea': '', 'areatype': 'N',
             'posttype': 'S', 'src': 'F', 'sortcolumn': '', 'sorttype': '', 'limit': '300', 'currentpage': page_no}
        url = url + urllib.urlencode(f)
        f = {
            'url': url
        }
        url = "http://hk.centanet.com/findproperty/BLL/Result_SearchHandler.ashx?" + urllib.urlencode(f)
        headers = {'Cookie': self.__cookie,
                   'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0',
                   'Accept': 'application/json, text/javascript, */*; q=0.01',
                   'Accept-Language': 'en-US,en;q=0.5',
                   'DNT': '1',
                   'Referer': 'http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/?mktid=HK&minprice=&maxprice=&minarea=&maxarea=&areatype=N&posttype=S&src=F',
                   'X-Requested-With': 'XMLHttpRequest'}
        print headers

        request = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(request)
        headers = response.info()
        for header in headers:
            print header, headers[header]

        if 'set-cookie' in headers:
            print 'old', self.__cookie
        set_cookie = headers['set-cookie']

        search_post_list = self.extract_cookie(set_cookie, 'SearchPostList')
        if self.__session_id is None:
            self.__session_id = self.extract_cookie(set_cookie, 'SessionID')

        session_params = []
        session_params.append('CultureInfo=TraditionalChinese')
        session_params.append('SessionID=' + (self.__session_id if self.__session_id is not None else ''))
        session_params.append('SearchPostList=' + search_post_list)
        session_params.append('ASP.NET_SessionId=' + '2tz1uuyqsmmb1ezm0mn2femi')
        self.__cookie = '; '.join(session_params)
        print 'new', self.__cookie
        print
        print
        html = response.read()

        j = json.loads(html)
        # print j['post']

        parser = CentanetParser()
        parser.start_over()
        parser.feed(j['post'])

        print len(parser.item_list), 'found'
        print parser.item_list[-1]
        row_count = 0
        for item in parser.item_list:
            house = House(SOURCE_TYPE_CENTANET)
            house.upsert(self.__db, item)
            if row_count < 20:
                row_count += 1
            else:
                row_count = 0
                self.__db.con.commit()

        if row_count > 0:
            self.__db.con.commit()

    def extract_cookie(self, s, key):
        pattern = r'(%s\=)(\S+)[;?]' % key
        groups = re.findall(pattern, s)
        if len(groups) == 0:
            return None
        return groups[0][1]


class CentanetParser(BaseParser):
    STATE_LOOK_FOR_START = 1
    STATE_LOOK_FOR_COMMUNITY = 2
    STATE_FOUND_COMMUNITY = 3
    STATE_LOOK_FOR_ADDRESS = 4
    STATE_LOOK_FOR_USE_AREA = 5
    STATE_FOUND_USE_AREA = 6
    STATE_LOOK_FOR_BUILD_AREA = 7
    STATE_FOUND_BUILD_AREA = 8
    STATE_LOOK_FOR_ROOM = 9
    STATE_FOUND_ROOM = 10
    STATE_LOOK_FOR_AGE = 11
    STATE_FOUND_AGE = 12
    STATE_LOOK_FOR_PRICE = 13
    STATE_FOUND_PRICE = 14

    __state = STATE_LOOK_FOR_START

    source_id = None

    __item = None

    item_list = []

    def start_over(self):
        self.item_list = []
        self.__state = self.STATE_LOOK_FOR_START

    def handle_starttag(self, tag, attrs):
        if self.hasAttr('postid', attrs):
            if self.__item is not None:
                self.item_list.append(self.__item)

            # fill in default values for item
            self.__item = {
                'source_type': SOURCE_TYPE_CENTANET,
                'area': None,
                'district': None,
                'floor': None,
                'hall': None,
                'refresh_time': time.time(),
                'source_url': None,
                'lat': None,
                'lng': None,
            }

            self.__item['source_id'] = self.getFromAttrs('postid', attrs)
            self.__state = self.STATE_LOOK_FOR_COMMUNITY
        elif self.__state == self.STATE_LOOK_FOR_COMMUNITY:
            if self.getFromAttrs("class", attrs) == 'ContentInfo_Left fLeft':
                self.__state = self.STATE_FOUND_COMMUNITY
        elif self.__state == self.STATE_LOOK_FOR_ADDRESS:
            if tag == 'span':
                s = self.getFromAttrs('title', attrs)
                s = s[0:s.rfind(' ')]
                self.__item['address'] = s
                self.__state = self.STATE_LOOK_FOR_USE_AREA
        elif self.__state == self.STATE_LOOK_FOR_USE_AREA:
            if tag == 'span':
                if self.getFromAttrs('class', attrs) == 'LargeString':
                    self.__state = self.STATE_FOUND_USE_AREA
        elif self.__state == self.STATE_LOOK_FOR_BUILD_AREA:
            if tag == 'span':
                if self.getFromAttrs('class', attrs) == 'LargeString':
                    self.__state = self.STATE_FOUND_BUILD_AREA
        elif self.__state == self.STATE_LOOK_FOR_ROOM:
            if tag == 'p':
                self.__state = self.STATE_FOUND_ROOM
        elif self.__state == self.STATE_LOOK_FOR_AGE:
            if tag == 'p':
                self.__state = self.STATE_FOUND_AGE
        elif self.__state == self.STATE_LOOK_FOR_PRICE:
            if self.getFromAttrs('class', attrs) == 'LargeString':
                self.__state = self.STATE_FOUND_PRICE
        pass

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        data = data.strip()
        if data == "":
            return

        if self.__state == self.STATE_FOUND_COMMUNITY:
            self.__item['community'] = data.strip()
            self.__state = self.STATE_LOOK_FOR_ADDRESS
        elif self.__state == self.STATE_FOUND_USE_AREA:
            self.__item['use_area'] = "".join(re.findall(r'\d+', data))
            self.__state = self.STATE_LOOK_FOR_BUILD_AREA
        elif self.__state == self.STATE_FOUND_BUILD_AREA:
            self.__item['build_area'] = "".join(re.findall(r'\d+', data))
            self.__state = self.STATE_LOOK_FOR_ROOM
        elif self.__state == self.STATE_FOUND_ROOM:
            self.__item['room'] = re.findall(r'\d+', data)[0]
            self.__state = self.STATE_LOOK_FOR_AGE
        elif self.__state == self.STATE_FOUND_AGE:
            self.__item['age'] = re.findall(r'\d+', data)[0]
            self.__state = self.STATE_LOOK_FOR_PRICE
        elif self.__state == self.STATE_FOUND_PRICE:
            self.__item['price'] = "".join(re.findall(r'\d+', data))
            self.__state = self.STATE_LOOK_FOR_PRICE


if __name__ == '__main__':
    parser = ParserCentanet()
    for i in range(1, 8):
        parser.fetch_page(i)
