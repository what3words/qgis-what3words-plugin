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
        params = {'words':words, 'format':'json'}
        return self.postRequest(self.host + '/v3/convert-to-coordinates', params)

    def convertTo3wa(self, lat='', lng='', format='json', language=None):
        coords = "%s,%s" % (lat, lng)
        params = {'coordinates':coords, 'format':'json', 'language':self.addressLanguage}
        return self.postRequest(self.host + '/v3/convert-to-3wa', params)	

    def getLanguages(self):
        return self.postRequest(self.host + '/v3/languages', dict())

    def postRequest(self, url, params):
        params.update({'key': self.apikey})
        encparams = urllib.parse.urlencode(params)
        url = url + '?' + encparams
        headers = {'X-W3W-Plugin':'what3words-QGIS/4.3 ()'}
        response, content = self.nam.request(url, headers=headers)
        response_json = json.loads(content)
        return response_json