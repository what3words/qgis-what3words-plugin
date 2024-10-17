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
    <p><code>convert_to_coord(w3w_address[, order='yx', delimiter=', ', crs='EPSG:4326', return_type='separate'])</code></p>

    <h4>Arguments:</h4>
    <ul>
        <li><i>w3w_address</i> &rarr; The what3words address to convert.</li>
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
        w3w_address = values[0]
        order = values[1] if num_args > 1 else 'yx'
        delimiter = values[2] if num_args > 2 else ', '
        crs = values[3] if num_args > 3 else 'EPSG:4326'
        return_type = values[4] if num_args > 4 else 'separate'
        
        w3w = get_w3w_api()
        result = w3w.convertToCoordinates(w3w_address)
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
    Convert latitude and longitude to a what3words address (3-word address).

    <h4>Syntax</h4>
    <p><b>convert_to_3wa( latitude, longitude[, language='en'] )</b></p>

    <h4>Arguments</h4>
    <p><i>latitude</i> &rarr; The latitude coordinate (y).</p>
    <p><i>longitude</i> &rarr; The longitude coordinate (x).</p>
    <p><i>language</i> &rarr; (Optional) The 2-letter ISO code for the language. Default is 'en' (English).</p>

    <h4>Output</h4>
    <p>This function returns the 3-word what3words address for the given coordinates.</p>

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
        return result['words']  # Return the 3-word address

    except Exception as e:
        parent.setEvalErrorString(f"Error converting to what3words address: {str(e)}")
        return None



def register_w3w_functions():
    """
    Register what3words functions.
    """
    QgsExpression.registerFunction(convert_to_3wa)
    QgsExpression.registerFunction(convert_to_coord)


def unregister_w3w_functions():
    """
    Unregister what3words functions.
    """
    QgsExpression.unregisterFunction('convert_to_3wa')
    QgsExpression.unregisterFunction('convert_to_coord')
