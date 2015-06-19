import json
import urllib
import urllib2
import time

import re
from hkhouse.core.db import HousingDB, House, SOURCE_TYPE_CENTANET
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
             'posttype': 'R', 'src': 'F', 'sortcolumn': '', 'sorttype': '', 'limit': -1, 'currentpage': page_no}
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
        print 'fetching', page_no

        request = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(request)
        headers = response.info()
        set_cookie = headers['set-cookie']
        search_post_list = self.extract_cookie(set_cookie, 'SearchPostList')
        if self.__session_id is None:
            self.__session_id = self.extract_cookie(set_cookie, 'SessionID')

        session_params = []
        session_params.append('CultureInfo=TraditionalChinese')
        session_params.append('SessionID=' + (self.__session_id if self.__session_id is not None else ''))
        session_params.append('SearchPostList=' + search_post_list if search_post_list is not None else '')
        session_params.append('ASP.NET_SessionId=' + '2tz1uuyqsmmb1ezm0mn2femi')
        self.__cookie = '; '.join(session_params)
        html = response.read()

        j = json.loads(html)
        # print j['post']
        self.process_page(j['post'])

    def process_page(self, html):
        parser = CentanetParser()
        parser.start_over()
        parser.feed(html)

        row_count = 0
        for item in parser.item_list:
            print item
            print

            house = House(SOURCE_TYPE_CENTANET)
            house.upsert(self.__db, item)
            if row_count < 20:
                row_count += 1
            else:
                row_count = 0
                self.__db.con.commit()

        if row_count > 0:
            self.__db.con.commit()
            pass

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
    STATE_LOOK_FOR_AREA_TYPE = 15
    STATE_FOUND_AREA_TYPE = 16
    STATE_LOOK_FOR_ROOM_AND_AGE = 17
    STATE_FOUND_PRICE_TYPE = 18

    __state = STATE_LOOK_FOR_START

    source_id = None

    __item = None

    item_list = None

    __error = False

    def start_over(self):
        self.item_list = []
        self.__state = self.STATE_LOOK_FOR_START

    def handle_starttag(self, tag, attrs):
        old_state = self.__state

        if self.hasAttr('postid', attrs):
            # if self.__item is not None:
            #     if not self.__error:
            #         self.item_list.append(self.__item)
            #     else:
            #         self.__error = False

            # fill in default values for item
            self.__item = {
                'source_type': SOURCE_TYPE_CENTANET,
                'area': None,
                'district': None,
                'floor': None,
                'hall': None,
                'refresh_time': time.time(),
                'source_url': '',
                'lat': None,
                'lng': None,
                'room': 0,
                'age': 0
            }

            self.__item['source_id'] = self.getFromAttrs('postid', attrs)
            self.__state = self.STATE_LOOK_FOR_COMMUNITY

            if self.__item['source_id'] == '14de1c60-42e2-46ed-a539-6b497a34f14c':
                a = 1
        elif self.__state == self.STATE_LOOK_FOR_COMMUNITY:
            if self.getFromAttrs("class", attrs) == 'ContentInfo_Left fLeft':
                self.__state = self.STATE_FOUND_COMMUNITY
        elif self.__state == self.STATE_LOOK_FOR_ADDRESS:
            if tag == 'span':
                s = self.getFromAttrs('title', attrs)
                s = s[0:s.rfind(' ')]
                self.__item['address'] = s.strip()
                self.__state = self.STATE_LOOK_FOR_AREA_TYPE
        elif self.__state == self.STATE_LOOK_FOR_AREA_TYPE:
            if tag == 'p':
                attr_class = self.getFromAttrs('class', attrs)
                if attr_class == 'ContentInfo_SizeStr fLeft':
                    self.__state = self.STATE_FOUND_AREA_TYPE
                elif 'ContentInfo_DetailStr_Lf' in attr_class:
                    self.__state = self.STATE_LOOK_FOR_ROOM_AND_AGE
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
        # elif self.__state == self.STATE_LOOK_FOR_PRICE:
        #     if self.getFromAttrs('class', attrs) == 'LargeString':
        #         self.__state = self.STATE_FOUND_PRICE
        elif self.__state == self.STATE_LOOK_FOR_ROOM_AND_AGE:
            if tag == 'span':
                if self.getFromAttrs('class', attrs) == 'ContentInfo_Final_SellPriceStr':
                    self.__state = self.STATE_LOOK_FOR_PRICE
        elif self.__state == self.STATE_LOOK_FOR_PRICE:
            if tag == 'span':
                if self.getFromAttrs('class', attrs) == 'ContentInfo_Final_SellPriceStr':
                    self.__state = self.STATE_FOUND_PRICE_TYPE

        pass

        # if old_state != self.__state:
        #     print 'from {old} to {current}'.format(old=old_state, current=self.__state)

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        data = data.strip()
        if data == "":
            return

        # try:
        if self.__state == self.STATE_FOUND_COMMUNITY:
            self.__item['community'] = data.strip()
            self.__state = self.STATE_LOOK_FOR_ADDRESS
        elif self.__state == self.STATE_FOUND_USE_AREA:
            self.__item['use_area'] = "".join(re.findall(r'\d+', data))
            self.__state = self.STATE_LOOK_FOR_BUILD_AREA
        elif self.__state == self.STATE_FOUND_BUILD_AREA:
            self.__item['build_area'] = "".join(re.findall(r'\d+', data))
            self.__state = self.STATE_LOOK_FOR_ROOM_AND_AGE
        # elif self.__state == self.STATE_FOUND_ROOM:
        #     self.__item['room'] = re.findall(r'\d+', data)[0]
        #     self.__state = self.STATE_LOOK_FOR_AGE
        # elif self.__state == self.STATE_FOUND_AGE:
        #     self.__item['age'] = re.findall(r'\d+', data)[0]
        elif self.__state == self.STATE_LOOK_FOR_PRICE:
            if data == u'\u79df':
                self.__state = self.STATE_FOUND_PRICE;
        elif self.__state == self.STATE_FOUND_PRICE:
            # price = int("".join(re.findall(r'\d+', data)))
            # self.__item['price'] = price if price > 5000 else price * 10000
            price = data.replace(',', '')
            # tenthousand_position = price.find('\xe8\x90\xac')
            tenthousand_position = price.find(u'\u842c')
            if tenthousand_position > 0:
                price = float(price[1:tenthousand_position]) * 10000
            else:
                price = price[1:]

            self.__item['price'] = price

            if self.__item is not None:
                if not self.__error:
                    self.item_list.append(self.__item)
                else:
                    self.__error = False

            self.__state = self.STATE_LOOK_FOR_START
        elif self.__state == self.STATE_FOUND_AREA_TYPE:
            # if data == '\xe5\xaf\xa6:':
            if data == u'\u5be6:':
                self.__state = self.STATE_LOOK_FOR_USE_AREA
            elif data == '\xe5\xbb\xba:':
                self.__state = self.STATE_LOOK_FOR_BUILD_AREA
        elif self.__state == self.STATE_LOOK_FOR_ROOM_AND_AGE:
            # if data.endswith('\xe5\xb9\xb4\xe6\xa8\x93\xe9\xbd\xa1'):
            if data.endswith(u'\u5e74\u6a13\u9f61'):
                self.__item['age'] = re.findall(r'\d+', data)[0]
            # elif '\xe6\x88\xbf' in data:
            elif u'\u623f' in data:
                self.__item['room'] = re.findall(r'\d+', data)[0]
        elif self.__state == self.STATE_FOUND_PRICE_TYPE:
            # if '\xe7\xa7\x9f' == data:
            if u'\u79df' == data:
                self.__state = self.STATE_FOUND_PRICE


if __name__ == '__main__':
    parser = ParserCentanet()
    for i in range(1, 300):
        parser.fetch_page(i)
