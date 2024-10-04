'''The MIT License (MIT)

Copyright (c) 2015 what3words

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import urllib.parse
import json
from qgiscommons2.network.networkaccessmanager import NetworkAccessManager
from qgis.utils import iface
from qgis.core import Qgis


class GeoCodeException(Exception):
    pass
		

class what3words(object):
    """what3words API"""

    def __init__(self, host='api.what3words.com', apikey='', addressLanguage=''):
        self.host = 'https://' + host
        self.apikey = apikey
        self.addressLanguage = addressLanguage
        self.nam = NetworkAccessManager()

    def convertToCoordinates(self, words='index.home.raft', format='json'):
        if isinstance(words, list):
            words = "%s.%s.%s" % (words[0], words[1], words[2])
        params = {'words':words, 'format':format}
        url = self.host + '/v3/convert-to-coordinates'
        return self.postRequest(url, params)

    def convertTo3wa(self, lat='', lng='', format='json', language=None):
        coords = "%s,%s" % (lat, lng)
        params = {'coordinates':coords, 'format':format, 'language':self.addressLanguage}
        url = self.host + '/v3/convert-to-3wa'
        return self.postRequest(url, params)	

    def getLanguages(self):
        url = self.host + '/v3/languages'
        return self.postRequest(url, dict())
    
    def getGridSection(self, bounding_box, format='json'):
        """
        Fetches the What3words grid for a given bounding box.
        
        :param bounding_box: A string in the format 'lat1,lng1,lat2,lng2'
        :param format: Response format, defaults to 'json'
        :return: The grid data from the What3words API.
        """
        params = {'bounding-box': bounding_box, 'format': format}
        url = self.host + '/v3/grid-section'
        return self.postRequest(url, params)

    def postRequest(self, url, params):
        params.update({'key': self.apikey})
        encparams = urllib.parse.urlencode(params)
        url = url + '?' + encparams
        headers = {'X-W3W-Plugin':'what3words-QGIS/4.3 ()'}
        response, content = self.nam.request(url, headers=headers)
        response_json = json.loads(content)
        return response_json