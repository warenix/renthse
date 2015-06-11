import json
import urllib
import urllib2
from hkhouse.db import HousingDB, SOURCE_TYPE_591, REVERSE_GEOCODING_STATUS_SUCCESS, REVERSE_GEOCODING_STATUS_FAIL, \
    REVERSE_GEOCODING_STATUS_PENDING
from hkhouse.opencage import OpenCage

__author__ = 'warenix'


class DBWorker(object):
    __db = None

    def __init__(self):
        self.__db = HousingDB()
        self.__db.init_db()

    def run(self):
        cur = self.__db.con.cursor()
        success = True
        while success:
            sql = 'select * from House where source_type={source_type} and reverse_geocoding_status={reverse_geocoding_status} limit 1'.format(
                source_type=SOURCE_TYPE_591,
                reverse_geocoding_status=REVERSE_GEOCODING_STATUS_PENDING
            )
            cur.execute(sql)
            row = cur.fetchone()
            if row is None:
                break
            success = self.process_item(row)

    def process_item(self, item):
        return False

    def get_cursor(self):
        return self.__db.con.cursor()

    def commit_cursor(self):
        self.__db.con.commit()


class ReverseGeocodingWorker(DBWorker):
    __reverse_geocoding_api = OpenCage()

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
                'source_type': SOURCE_TYPE_591,
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
                'source_type': SOURCE_TYPE_591,
                'source_id': item['source_id'],
                'reverse_geocoding_status': REVERSE_GEOCODING_STATUS_FAIL
            }
        cur = self.get_cursor()
        cur.execute(sql, d)
        self.commit_cursor()

        return remaining > 0


worker = ReverseGeocodingWorker()
worker.run()
