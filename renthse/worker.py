import urllib

from renthse.core.db import HousingDB, REVERSE_GEOCODING_STATUS_SUCCESS, REVERSE_GEOCODING_STATUS_FAIL, \
    REVERSE_GEOCODING_STATUS_PENDING, SOURCE_TYPE_CENTANET
from renthse.extapi.opencage import OpenCage

__author__ = 'warenix'


class DBWorker(object):
    __db = None
    __source_type = None

    def __init__(self, source_type):
        self.__db = HousingDB()
        self.__db.init_db()
        self.__source_type = source_type

    def run(self):
        sql = self.get_process_item_sql()

        if sql is not None:
            success = True

            cur = self.__db.con.cursor()
            while success:
                cur.execute(sql)
                row = cur.fetchone()
                if row is None:
                    break
                success = self.process_item(row)

    def get_process_item_sql(self):
        ''' select one item form db. the item will be passed to process_item()
        :param item:
        :return: None if no item is selected
        '''
        return None

    def process_item(self, item):
        ''' process an item selected from db.
        :param item: item selected from get_process_item_sql()
        :return: True if there's more item to be processed.
        '''
        return False

    def get_cursor(self):
        return self.__db.con.cursor()

    def commit_cursor(self):
        self.__db.con.commit()

    def get_source_type(self):
        return self.__source_type


class ReverseGeocodingWorker(DBWorker):
    __reverse_geocoding_api = OpenCage()

    def get_process_item_sql(self):
        sql = 'select * from House where reverse_geocoding_status={reverse_geocoding_status} limit 1'.format(
            source_type=self.get_source_type(),
            reverse_geocoding_status=REVERSE_GEOCODING_STATUS_PENDING
        )
        return sql

    def process_item(self, item):
        q = u"{address}".format(address=item['address'])
        lat, lng, remaining = self.__reverse_geocoding_api.reverse_geocoding(urllib.quote(q.encode('utf-8')))
        print q, lat, lng, remaining

        sql = None
        if lat is not None and lng is not None:
            sql = """UPDATE House
             SET reverse_geocoding_status=:reverse_geocoding_status,
             lat=:lat, lng=:lng
            WHERE source_type = :source_type and source_id = :source_id"""
            d = {
                'source_type': self.get_source_type(),
                'source_id': item['source_id'],
                'lat': lat,
                'lng': lng,
                'reverse_geocoding_status': REVERSE_GEOCODING_STATUS_SUCCESS
            }

        else:
            sql = """UPDATE House
             SET reverse_geocoding_status=:reverse_geocoding_status
            WHERE source_type = :source_type and source_id = :source_id"""
            d = {
                'source_type': self.get_source_type(),
                'source_id': item['source_id'],
                'reverse_geocoding_status': REVERSE_GEOCODING_STATUS_FAIL
            }
        cur = self.get_cursor()
        cur.execute(sql, d)
        self.commit_cursor()

        return remaining > 0


if __name__ == '__main__':
    worker = ReverseGeocodingWorker(SOURCE_TYPE_CENTANET)
    worker.run()
