import json
import urllib2
import re
import time
from hkhouse.db import HousingDB, House, SOURCE_TYPE_CENTANET
from hkhouse.htmlparser import BaseParser

__author__ = 'warenix'


class ParserCentanet(object):
    __db = None
    __row_count = 0

    def __init__(self):
        self.__db = HousingDB()
        self.__db.init_db()

    def fetch_page(self, page_no):
        url = "http://hk.centanet.com/findproperty/BLL/Result_SearchHandler.ashx?url=http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/?mktid=HK&minprice=&maxprice=&minarea=&maxarea=&areatype=N&posttype=S&src=F&sortcolumn=&sorttype=&limit={limit}&currentpage={page_no}".format(
            page_no=page_no,
            limit=300)

        # http://hk.centanet.com/findproperty/BLL/Result_SearchHandler.ashx?url=http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/?mktid=HK&minprice=&maxprice=&minarea=&maxarea=&areatype=N&posttype=S&src=F&sortcolumn=&sorttype=&limit=300&currentpage=2
        # http://hk.centanet.com/findproperty/BLL/Result_SearchHandler.ashx?url=http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/?mktid=HK&minprice=&maxprice=&minarea=&maxarea=&areatype=N&posttype=S&src=F&sortcolumn=&sorttype=&limit=300&currentpage=5

        print url;
        return

        headers = {}
        request = urllib2.Request(url, headers=headers)
        html = urllib2.urlopen(request).read()

        j = json.loads(html)
        # print j['post']

        parser = CentanetParser()
        parser.feed(j['post'])

        print len(parser.item_list), 'found'
        print parser.item_list[0]
        # for item in parser.item_list:
        #     house = House(SOURCE_TYPE_CENTANET)
        #     house.upsert(self.__db, item)
        # self.__db.con.commit()


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
            self.__item['community'] = data
            self.__state = self.STATE_LOOK_FOR_ADDRESS
        elif self.__state == self.STATE_FOUND_USE_AREA:
            self.__item['use_area'] = data
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
    for i in range(1, 3):
        parser.fetch_page(i)
