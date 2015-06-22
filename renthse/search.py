import os
import sys
sys.path.insert(1,os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from renthse.core.db import HousingDB

__author__ = 'warenix'


class Search(object):
    __db = None
    __row_count = 0

    def __init__(self):
        self.__db = HousingDB()
        self.__db.init_db()

    def pick_from_rect(self, center, delta):
        cur = self.__db.con.cursor()
        x, y = center[0], center[1]
        dx, dy = delta[0], delta[1]
        rect = 'lat >= %f and lat <= %f and lng >= %f and lng <= %f' % (x - dx, x + dx, y - dy, y + dy)
        sql = ''' select * from house where price <= 12000 and room >= 2 and use_area > 200
 and {rect}
 order by price desc '''.format(rect=rect);
        cur.execute(sql)
        for row in cur.fetchall():
            print row


if __name__ == '__main__':
    search = Search()
    search.pick_from_rect((22.279793, 114.222914), (0.010841, 0.015450))
