from qgis.core import Qgis, QgsExpression, QgsGeometry, QgsPointXY, QgsMessageLog, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.utils import qgsfunction
from qgis.PyQt.QtCore import QVariant
from qgiscommons2.settings import pluginSetting
from what3words.w3w import what3words

group_name = "what3words Tools"

# Define EPSG:4326 for transformations
epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

def transform_coords(y, x, crs):
    """
    Transform the coordinates from a given CRS to EPSG:4326.
    
    Arguments:
    - y: Latitude or Y coordinate.
    - x: Longitude or X coordinate.
    - crs: Source coordinate reference system (e.g., 'EPSG:3857').
    
    Returns:
    - Transformed (lat, lon) as (y, x) in EPSG:4326.
    """
    coord_crs = QgsCoordinateReferenceSystem(crs)
    transform = QgsCoordinateTransform(coord_crs, epsg4326, QgsProject.instance())
    transformed_pt = transform.transform(x, y)
    return transformed_pt.y(), transformed_pt.x()  # Return lat, lon (y, x in EPSG:4326)


def get_w3w_api():
    """
    Fetch the API key from plugin settings.
    """
    apiKey = pluginSetting("apiKey")
    if apiKey is None or apiKey == "":
        raise ValueError("API key not set in plugin settings.")
    return what3words(apikey=apiKey)


@qgsfunction(-1, group=group_name)
def convert_to_coord(values, feature, parent):
    """
    Convert a what3words address to latitude and longitude

    <h4>Syntax</h4>
    <p><b>convert_to_coord(what3words[, order='yx', delimiter=', ', crs='EPSG:4326', return_type='separate'])</b></p>

    <h4>Arguments:</h4>
    <ul>
        <li><i>what3words</i> &rarr; The what3words address to convert.</li>
        <li><i>order</i> (optional) &rarr; 'yx' for latitude, longitude or 'xy' for longitude, latitude. Default is 'yx'.</li>
        <li><i>delimiter</i> (optional) &rarr; Delimiter for string output. Default is ', '. Used if <i>return_type</i> is 'string'.</li>
        <li><i>crs</i> (optional) &rarr; The coordinate reference system of the input coordinates. Default is 'EPSG:4326'.</li>
        <li><i>return_type</i> (optional) &rarr; 'string' returns coordinates as a comma-separated string. 'separate' (default) returns [lat, lon] as a list.</li>
    </ul>

    <h4>Returns:</h4>
    <p>If <i>return_type</i> is 'separate', the function returns latitude and longitude as separate values in a list. If 'string', returns a string of lat, lon with the given delimiter.</p>

    <h4>Example usage:</h4>
    <ul>
        <li><code>convert_to_coord("filled.count.soap")</code> &rarr; Returns [lat, lon] in EPSG:4326 format.</li>
        <li><code>convert_to_coord("filled.count.soap", 'string')</code> &rarr; Returns "51.520847,-0.195521".</li>
        <li><code>convert_to_coord("filled.count.soap", 'xy', ', ', 'EPSG:3857', 'string')</code> &rarr; Converts coordinates to EPSG:3857 and returns as a string.</li>
    </ul>
    """
    num_args = len(values)
    if num_args < 1 or num_args > 5:
        parent.setEvalErrorString("Error: invalid number of arguments")
        return
    
    try:
        what3words = values[0]
        order = values[1] if num_args > 1 else 'yx'
        delimiter = values[2] if num_args > 2 else ', '
        crs = values[3] if num_args > 3 else 'EPSG:4326'
        return_type = values[4] if num_args > 4 else 'separate'
        
        w3w = get_w3w_api()
        result = w3w.convertToCoordinates(what3words)
        lat = result['coordinates']['lat']
        lon = result['coordinates']['lng']
        
        # Transform coordinates to the required CRS
        if crs and crs != 'EPSG:4326':
            lat, lon = transform_coords(lat, lon, crs)

        # Handle order of lat/lon
        coords = [lat, lon] if order == 'yx' else [lon, lat]

        # Return string or list based on return_type
        if return_type == 'string':
            return f"{coords[0]}{delimiter}{coords[1]}"
        else:
            return coords
    except Exception as e:
        parent.setEvalErrorString(f"Error converting to coordinates: {str(e)}")
        return None


@qgsfunction(-1, group=group_name)
def convert_to_3wa(values, feature, parent):
    """
    Convert latitude and longitude to a what3words address (3 word address).

    <h4>Syntax</h4>
    <p><b>convert_to_3wa( latitude, longitude[, language='en'] )</b></p>

    <h4>Arguments</h4>
    <p><i>latitude</i> &rarr; The latitude coordinate (y).</p>
    <p><i>longitude</i> &rarr; The longitude coordinate (x).</p>
    <p><i>language</i> &rarr; (Optional) The 2-letter ISO code for the language. Default is 'en' (English).</p>

    <h4>Output</h4>
    <p>This function returns the 3 word what3words address for the given coordinates.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>convert_to_3wa(51.520847, -0.195521)</b> &rarr; ///filled.count.soap</li>
      <li><b>convert_to_3wa(51.520847, -0.195521, 'es')</b> &rarr; ///caja.contar.jabón</li>
    </ul>

    <p>If you encounter errors during conversion, check the API key and coordinates.</p>
    """
    try:
        # Ensure latitude and longitude are provided
        if len(values) < 2:
            parent.setEvalErrorString("Error: Latitude and longitude must be provided.")
            return

        lat = values[0]
        lon = values[1]
        language = values[2] if len(values) > 2 else "en"  # Default to English if no language provided

        w3w = get_w3w_api()  # Get the what3words API key from settings
        result = w3w.convertTo3wa(lat, lon, language=language)
        return result['words']  # Return the 3 word address

    except Exception as e:
        parent.setEvalErrorString(f"Error converting to what3words address: {str(e)}")
        return None


@qgsfunction(-1, group="what3words Tools")
def change_w3w_language(values, feature, parent):
    """
    Change the language of a what3words address.

    <h4>Syntax</h4>
    <p><b>change_w3w_language( what3words, target_language )</b></p>

    <h4>Arguments</h4>
    <p><i>what3words</i> &rarr; The original what3words address (e.g., 'filled.count.soap').</p>
    <p><i>target_language</i> &rarr; The 2-letter ISO code for the target language (e.g., 'es' for Spanish).</p>

    <h4>Output</h4>
    <p>This function returns the 3 word what3words address in the specified language.</p>

    <h4>Example usage</h4>
    <ul>
      <li><b>change_w3w_language( 'filled.count.soap', 'es' )</b> &rarr; ///caja.contar.jabón</li>
      <li><b>change_w3w_language( 'caja.contar.jabón', 'en' )</b> &rarr; ///filled.count.soap</li>
    </ul>

    <p>If you encounter errors, ensure the API key is valid and the input what3words address is correct.</p>
    """
    try:
        # Ensure both the w3w address and target language are provided
        if len(values) < 2:
            parent.setEvalErrorString("Error: what3words address and target language must be provided.")
            return

        what3words = values[0]
        target_language = values[1]  # Target language code (e.g., 'es', 'fr')

        # Get the what3words API key from settings
        w3w = get_w3w_api()

        # Step 1: Convert the original w3w address back to coordinates
        result = w3w.convertToCoordinates(what3words)
        lat = result['coordinates']['lat']
        lon = result['coordinates']['lng']

        # Step 2: Convert the coordinates back to a what3words address in the target language
        translated_result = w3w.convertTo3wa(lat, lon, language=target_language)
        return translated_result['words']

    except Exception as e:
        parent.setEvalErrorString(f"Error changing language: {str(e)}")
        return None


@qgsfunction(-1, group=group_name)
def autosuggest_w3w(values, feature, parent):
    """
    Get autosuggestions for an incomplete what3words address, allowing additional options for country, focus, bounding box, circle, and polygon.

    <h4>Syntax</h4>
    <p><b>autosuggest_w3w</b>(<i>what3words, rank[, country, bbox, circle, polygon, focus]</i>)</p>

    <h4>Arguments</h4>
    <p><i>what3words</i> &rarr; the incomplete what3words address to get suggestions for (e.g., 'filled.count.so').</p>
    <p><i>rank</i> &rarr; the rank of the desired suggestion (e.g., 1 for the top suggestion).</p>

    <p><i>country</i> &rarr; (optional) restrict results to a specific country using the ISO 3166-1 alpha-2 country code (e.g., 'GB').</p>
    <p><i>bbox</i> &rarr; (optional) restrict results to within a bounding box, format 'south_lat,west_lng,north_lat,east_lng'.</p>
    <p><i>circle</i> &rarr; (optional) restrict results to within a circle, format 'lat,lng,radius_km'.</p>
    <p><i>polygon</i> &rarr; (optional) restrict results to within a polygon, format 'lat1,lng1|lat2,lng2|...'.</p>
    <p><i>focus</i> &rarr; (optional) prioritize results around a specific point, format 'lat,lng'.</p>

    <h4>Example usage</h4>

    <p><b>1. Only what3words Address and Rank:</b><br>
    autosuggest_w3w('filled.count.so', 1)</p>

    <p><b>2. what3words Address and Rank + Focus:</b><br>
    autosuggest_w3w('filled.count.so', 1, '', '', '', '', '51.5074,-0.1278')</p>

    <p><b>3. what3words Address and Rank + Country:</b><br>
    autosuggest_w3w('filled.count.so', 1, 'GB')</p>

    <p><b>4. what3words Address and Rank + Bounding Box (BBOX):</b><br>
    autosuggest_w3w('filled.count.so', 1, '', '51.28,-0.489,51.686,0.236')</p>

    <p><b>5. what3words Address and Rank + Polygon:</b><br>
    autosuggest_w3w('filled.count.so', 1, '', '', '', '51.521,-0.343,52.6,2.3324,54.234,8.343,51.521,-0.343')</p>

    <p><b>6. what3words Address and Rank + Circle:</b><br>
    autosuggest_w3w('filled.count.so', 1, '', '', '51.5074,-0.1278,5')</p>

    <p><b>7. All Together (Using All Options):</b><br>
    autosuggest_w3w('d.d.d', 1, 'GB','-0.197277,51.520660,-0.195347,51.521612','51.521136,-0.196312,5','51.521612,-0.197277,51.520660,-0.197277,51.520660,-0.195347,51.521612,-0.195347,51.521612,-0.197277', '51.521436,-0.196612')</p>

    <h4>Output</h4>
    <p>The function returns the autosuggestion for the given incomplete what3words address and rank. If insufficient suggestions are available, an error will be raised.</p>
    """
    # Validate input arguments
    if len(values) < 2:
        parent.setEvalErrorString("Error: Insufficient number of arguments.")
        return None

    input_address = values[0]
    rank = int(values[1])
    
    # Optional arguments for clipping
    country = values[2] if len(values) > 2 else None
    bbox = values[3] if len(values) > 3 else None
    circle = values[4] if len(values) > 4 else None
    polygon = values[5] if len(values) > 5 else None
    focus = values[6] if len(values) > 6 else None

    # Prepare API request
    apiKey = pluginSetting("apiKey")
    if not apiKey:
        parent.setEvalErrorString("Error: API key not set.")
        return None

    w3w = what3words(apikey=apiKey)

    # Construct API parameters
    try:
        # Make API call to autosuggest with relevant options
        response = w3w.autosuggest(
            input_address,
            clip_to_country=country,
            clip_to_bounding_box=bbox,
            clip_to_circle=circle,
            clip_to_polygon=polygon,
            focus=focus
        )

        # Check if suggestions exist
        if 'suggestions' not in response or len(response['suggestions']) < rank:
            raise ValueError(f"Insufficient suggestions for rank {rank}.")

        # Return the requested suggestion based on rank
        suggestion = response['suggestions'][rank - 1]  # Rank starts from 1
        return suggestion['words']

    except Exception as e:
        parent.setEvalErrorString(f"Error: {str(e)}")
        return None


def register_w3w_functions():
    """
    Register what3words functions.
    """
    QgsExpression.registerFunction(convert_to_3wa)
    QgsExpression.registerFunction(convert_to_coord)
    QgsExpression.registerFunction(change_w3w_language)
    QgsExpression.registerFunction(autosuggest_w3w)


def unregister_w3w_functions():
    """
    Unregister what3words functions.
    """
    QgsExpression.unregisterFunction('convert_to_3wa')
    QgsExpression.unregisterFunction('convert_to_coord')
    QgsExpression.registerFunction(change_w3w_language)
    QgsExpression.registerFunction(autosuggest_w3w)
