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
import urllib
import urllib2
import json

class what3words(object):
    """what3words API"""

    def __init__(self, host='api.what3words.com', apikey=''):
        self.host = 'http://' + host
        self.apikey = apikey

    def getPosition(self, words='*libertytech', onewordpassword='',
                    lang='en', corners='false', email='', password=''):
        if isinstance(words, list):
            words = "%s.%s.%s" % (words[0], words[1], words[2])
            print "string is: %s" % (words)
        params = { 'corners': corners, 'string': words }
        if (onewordpassword != ''):
            params.update({'onewordpassword', onewordpassword,
                           'email', email,
                           'password', password});
        return self.postRequest(self.host + '/w3w', params)

    def getWords(self, lat='', lng='', corners='false', lang='en'):
        position = "%s,%s" % (lat, lng)
        params = { 'position': position, 'corners': corners, 'lang': lang }
        return self.postRequest(self.host + '/position', params)

    def getLanguages(self):
        return self.postRequest(self.host + '/get-languages', dict())

    def postRequest(self, url, params):
        params.update({'key': self.apikey})
        encparams = urllib.urlencode(params)
        try: response = urllib.urlopen(url, encparams).read()
        except URLError as e:
            raise e
        return json.loads(response)
