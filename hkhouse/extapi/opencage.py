import json
import urllib2

__author__ = 'warenix'


class OpenCage(object):
    __key = None

    def reverse_geocoding(self, q):
        if self.__key is None:
            raise ValueError('No api key. Please obtain one at https://developer.opencagedata.com/')
        url = '''https://api.opencagedata.com/geocode/v1/json?q={q}&key={key}&pretty=1'''.format(
            q=q,
            key=self.__key)
        print url

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }
        request = urllib2.Request(url, headers=headers)
        html = urllib2.urlopen(request).read()
        j = json.loads(html)

        lat, lng, remaining = None, None, j['rate']['remaining']

        for result in j['results']:
            geometry = result['geometry'] if 'geometry' in result else None
            if geometry is not None:
                lat = geometry['lat']
                lng = geometry['lng']

        return lat, lng, remaining
