__author__ = 'warenix'
import sqlite3 as lite

SOURCE_TYPE_591 = 1

REVERSE_GEOCODING_STATUS_PENDING = 0
REVERSE_GEOCODING_STATUS_FAIL = 1
REVERSE_GEOCODING_STATUS_SUCCESS = 2


class HousingDB(object):
    con = None

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def __init__(self):
        con = lite.connect('test.db')
        con.row_factory = self.dict_factory
        self.con = con

    def init_db(self):
        with self.con:
            cur = self.con.cursor()

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
                        "refresh_time INTEGER,"
                        "lat Decimal(9,6),"
                        "lng Decimal(9,6),"
                        "reverse_geocoding_status INTEGER DEFAULT 0"
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

    def upsert(self, db, d):
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
        refresh_time,
        lat,lng
        ) VALUES (
        :source_type, :source_id,
        :area, :district,
        :community, :address, :floor,
        :room, :hall, :age,
        :use_area, :build_area,
        :price,
        :source_url,
        :refresh_time,
        (SELECT lat FROM HOUSE WHERE source_type=:source_type and source_id=:source_id),
        (SELECT lng FROM HOUSE WHERE source_type=:source_type and source_id=:source_id)
        )
        """
        cur.execute(sql, d)
        print cur.lastrowid


if __name__ == '__main__':
    db = HousingDB()
