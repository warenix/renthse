__author__ = 'warenix'
import sqlite3 as lite

SOURCE_TYPE_591 = 1


class HousingDB(object):
    con = None

    def __init__(self):
        self.con = lite.connect('test.db')

    def init_db(self):
        with self.con:
            cur = self.con.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS Rent ("
                        "rent_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "source_type INTEGER,"
                        "source_id INTEGER"
                        ")")
            cur.execute("CREATE TABLE IF NOT EXISTS House("
                        "house_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                        "source_type INTEGER,"
                        "source_id INTEGER,"
                        "area TEXT,"
                        "district TEXT,"
                        "community TEXT,"
                        "address TEXT,"
                        "floor TEXT,"
                        "room INTEGER,"
                        "hall INTEGER,"
                        "age INTEGER,"
                        "use_area INTEGER,"
                        "build_area INTEGER,"
                        "price INTEGER,"
                        "source_url TEXT,"
                        "refresh_time INTEGER"
                        ")")
            cur.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_house_1 ON House (
            source_type, source_id
            )
            ''')


class House(object):
    __source_type = None
    __row = None

    def __init__(self, source_type):
        self.__source_type = source_type

    def load(self, db, source_id):
        cur = db.con.cursor()
        cur.execute("select * from House where source_type={source_type} and source_id={source_id}".format(
            source_type=self.__source_type,
            source_id=source_id
        ))
        for row in cur.fetchall():
            self.__row = row

    def is_loaded(self):
        return self.__row is not None

    def upsert(self, db, item):
        cur = db.con.cursor()
        sql = u"""
        INSERT OR REPLACE INTO House (
        source_type, source_id,
        area, district,
        community, address, floor,
        room, hall, age,
        use_area, build_area,
        price,
        source_url,
        refresh_time
        ) VALUES (
        :source_type, :source_id,
        :area, :district,
        :community, :address, :floor,
        :room, :hall, :age,
        :use_area, :build_area,
        :price,
        :source_url,
        :refresh_time)
        """
        d = {
            'source_type': self.__source_type,
            'source_id': item['post_id'],
            'area': item['area'].strip(),
            'district': item['district'].strip(),
            'community': item['community'].strip(),
            'address': item['address'].strip(),
            'floor': item['floor'][:-1],
            'room': item['room'],
            'hall': item['hall'],
            'age': item['age'],
            'use_area': item['use_area_str'][:-1],
            'build_area': item['build_area_str'][:-1],
            'price': item['price_str'].replace(',', '')[:-1],
            'source_url': item['detailUrl'],
            'refresh_time': item['refreshtime']
        }

        cur.execute(sql, d)
        print cur.lastrowid


if __name__ == '__main__':
    db = HousingDB()
