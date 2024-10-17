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
import re
from qgiscommons2.network.networkaccessmanager import NetworkAccessManager
from qgis.utils import iface
from qgis.core import Qgis

W3W_PLUGIN_VERSION_NUMBER = '4.4'
W3W_PLUGIN_VERSION = f'what3words-QGIS/{W3W_PLUGIN_VERSION_NUMBER} ()'

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
        """
        Convert a what3words address to coordinates and return the bounding square and coordinates.

        :param words: The what3words address to convert
        :param format: The response format (default is 'json')
        :return: The square and coordinates of the what3words address
        """
        if isinstance(words, list):
            words = "%s.%s.%s" % (words[0], words[1], words[2])
        params = {'words': words, 'format': format}
        url = self.host + '/v3/convert-to-coordinates'
        response_json = self.postRequest(url, params)

        if 'square' in response_json:
            return {
                'square': response_json['square'],
                'coordinates': response_json['coordinates'],
                'nearestPlace': response_json.get('nearestPlace', ''),
                'words': response_json.get('words', ''),
                'country': response_json.get('country', ''),
                'language': response_json.get('language', '')
            }
        else:
            error_message = response_json.get('error', 'Failed to retrieve the what3words address square')
            raise GeoCodeException(error_message)

    def convertTo3wa(self, lat='', lng='', format='json', language=None):
        """
        Convert coordinates to a what3words address and return the bounding square and what3words address.

        :param lat: Latitude to convert
        :param lng: Longitude to convert
        :param format: The response format (default is 'json')
        :param language: The language for the what3words address (optional)
        :return: The square, what3words address, and coordinates
        """
        coords = "%s,%s" % (lat, lng)
        params = {'coordinates': coords, 'format': format, 'language': language or self.addressLanguage}
        url = self.host + '/v3/convert-to-3wa'
        response_json = self.postRequest(url, params)

        if 'square' in response_json:
            return {
                'square': response_json['square'],
                'words': response_json['words'],
                'nearestPlace': response_json.get('nearestPlace', ''),
                'country': response_json.get('country', ''),
                'language': response_json.get('language', ''),
                'coordinates': response_json['coordinates'] 
            }
        else:
            error_message = response_json.get('error', 'Failed to retrieve the coordinates for what3words address')
            raise GeoCodeException(error_message)

    def getLanguages(self):
        """
        Retrieve the available languages for what3words addresses.

        :return: A list of available languages.
        """
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

    def autosuggest(self, input_text, format='json', language=None, focus=None, clip_to_country=None, clip_to_bounding_box=None, clip_to_circle=None, clip_to_polygon=None, input_type=None, prefer_land=None, locale=None):
        """
        Fetches suggestions for a partial what3words address.
        Parameters:
        - input_text (str): The full or partial 3 word address to obtain suggestions for.
        - format (str): The format of the response, defaults to 'json'.
        - language (str): Optional, the language of the suggestions (ISO 639-1 code).
        - focus (str): Optional, latitude and longitude to prioritize suggestions near a location.
        - clip_to_country (str): Optional, comma-separated list of country codes to restrict results to.
        - clip_to_bounding_box (str): Optional, restrict results to a bounding box (south_lat,west_lng,north_lat,east_lng).
        - clip_to_circle (str): Optional, restrict results to a circle (lat,lng,radius_in_km).
        - clip_to_polygon (str): Optional, restrict results to a polygon (comma-separated lat,lng pairs).
        - input_type (str): Optional, input type (default is 'text').
        - prefer_land (bool): Optional, prefer results on land (true/false).
        - locale (str): Optional, locale for specific language variants.
        
        Returns:
        - JSON response containing the suggestions.
        """
        params = {
            'input': input_text,
            'format': format,
            'language': language or self.addressLanguage
        }
        
        # Add optional parameters if provided
        if focus:
            params['focus'] = focus
        if clip_to_country:
            params['clip-to-country'] = clip_to_country
        if clip_to_bounding_box:
            params['clip-to-bounding-box'] = clip_to_bounding_box
        if clip_to_circle:
            params['clip-to-circle'] = clip_to_circle
        if clip_to_polygon:
            params['clip-to-polygon'] = clip_to_polygon
        if input_type:
            params['input-type'] = input_type
        if prefer_land is not None:
            params['prefer-land'] = str(prefer_land).lower()  # Convert boolean to string
        if locale:
            params['locale'] = locale

        url = self.host + '/v3/autosuggest'
        return self.postRequest(url, params)
    
    def is_possible_3wa(self, text: str) -> bool:
        """
        Determines if the string passed in is in the form of a possible three-word address.
        :param text: Text to check
        :return: True if possible 3 word address, False otherwise
        """
        regex_match = r"^\/*(?:[^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]{1,}[.｡。･・︒។։။۔።।][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]{1,}[.｡。･・︒។։۔።।][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]{1,}|[<.,>?\/\";:£§º©®\s]+[.｡。･・︒។։။۔።।][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]+|[^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]+([\u0020\u00A0][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]+){1,3}[.｡。･・︒។։۔።।][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]+([\u0020\u00A0][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]+){1,3}[.｡。･・︒។։။۔።।][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]+([\u0020\u00A0][^0-9`~!@#$%^&*()+\-_=\[\{\]}\\|'<>.,?\/\";:£§º©®\s]+){1,3})$"
        return re.match(regex_match, text) is not None

    def is_valid_3wa(self, text: str) -> bool:
        """
        Determines if the string passed in is a real three-word address by calling the API.
        :param text: Text to check
        :return: True if valid 3 word address, False otherwise
        """
        if self.is_possible_3wa(text):
            result = self.w3w.autosuggest(text, n_results=1)  # Check for the top result
            if result["suggestions"] and result["suggestions"][0]["words"] == text:
                return True
        return False

    def postRequest(self, url, params):
        """
        Makes an HTTP request to the what3words API and handles errors appropriately.

        :param url: The URL for the API endpoint
        :param params: The parameters for the request
        :return: The JSON response from the API or raises GeoCodeException on failure
        """
        params.update({'key': self.apikey})
        encparams = urllib.parse.urlencode(params)
        url = url + '?' + encparams
        headers = {'X-W3W-Plugin': W3W_PLUGIN_VERSION}  # Use the centralized plugin version

        try:
            response, content = self.nam.request(url, headers=headers)
            response_json = json.loads(content)
            
            if response.status == 200:
                return response_json
            else:
                if 'error' in response_json:
                    error_code = response_json['error'].get('code', 'UnknownError')
                    error_message = response_json['error'].get('message', 'Unknown error occurred')
                    full_error_message = f"{error_code}: {error_message}"
                else:
                    full_error_message = response.reason

                iface.messageBar().pushMessage("what3words", f"API error: {full_error_message}", level=Qgis.Critical, duration=5)
                raise GeoCodeException(f"API error: {full_error_message}")

        except Exception as e:
            iface.messageBar().pushMessage("what3words", f"Request failed: {str(e)}", level=Qgis.Critical, duration=5)
            raise GeoCodeException(f"Request failed: {str(e)}")