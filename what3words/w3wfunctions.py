from qgis.core import Qgis, QgsExpression, QgsGeometry, QgsPointXY, QgsMessageLog
from qgis.utils import qgsfunction
from qgis.PyQt.QtCore import QVariant
from qgiscommons2.settings import pluginSetting
from what3words.w3w import what3words


group_name = "what3words"

# Define EPSG:4326 for transformations
epsg4326 = "EPSG:4326"


def get_w3w_api():
    """
    Fetch the API key from plugin settings.
    """
    apiKey = pluginSetting("apiKey")
    if apiKey is None or apiKey == "":
        raise ValueError("API key not set in plugin settings.")
    return what3words(apikey=apiKey)

@qgsfunction(args='auto', group='what3words')
def convert_to_coord(w3w_address, feature, parent):
    """
    Convert a what3words address to latitude and longitude, and return them as two separate values (latitude, longitude).
    
    <h4>Syntax</h4>
    <p><b><code>convert_to_coord(w3w_address)</code></p></b>
    
    <p>This function returns both latitude and longitude from a what3words address. To store these values in two separate fields
    in QGIS with type double (length and precision 0), follow the instructions below:</p>

    <ol>
    <li>Open the Field Calculator in QGIS.</li>
    <li>Create a new field for latitude with the following parameters:
      <ul>
        <li>Output field name: <code>latitude</code></li>
        <li>Output field type: <code>Decimal (double)</code></li>
        <li>Precision: <code>0</code></li>
        <li>Expression: <code>convert_to_coord("w3w_address")[0]</code> (This extracts the latitude part)</li>
      </ul>
    </li>
    
    <li>Create another field for longitude:
      <ul>
        <li>Output field name: <code>longitude</code></li>
        <li>Output field type: <code>Decimal (double)</code></li>
        <li>Precision: <code>0</code></li>
        <li>Expression: <code>convert_to_coord("w3w_address")[1]</code> (This extracts the longitude part)</li>
      </ul>
    </li>
    </ol>
    
    <p>If the what3words address conversion fails, both latitude and longitude fields will contain <code>NULL</code> values.</p>
    """
    try:
        w3w = get_w3w_api()
        result = w3w.convertToCoordinates(w3w_address)
        lat = result['coordinates']['lat']
        lon = result['coordinates']['lng']
        return [lat, lon]
    except Exception as e:
        parent.setEvalErrorString(f"Error converting to coordinates: {str(e)}")
        return None

@qgsfunction(args='auto', group='what3words')
def convert_to_3wa(lat, lon, feature, parent):
    """
    Convert latitude and longitude to a what3words address (what3words address).

    <h4>Syntax</h4>
    <p><b>convert_to_3wa(lat, lon)</b></p>
    
    <p>This function takes latitude and longitude as inputs and returns the corresponding what3words address.</p>

    <p><b>Instructions for using this function in QGIS:</b></p>
    
    <ol>
    <li>Open the Field Calculator in QGIS.</li>
    <li>Create a new field for the what3words address with the following parameters:
      <ul>
        <li>Output field name: <code>w3w_address</code></li>
        <li>Output field type: <code>Text (string)</code></li>
        <li>Length: <code>255</code> (or a sufficient length to hold the what3words address)</li>
        <li>Expression: <code>convert_to_3wa("latitude", "longitude")</code></li>
        <li>Replace <code>"latitude"</code> and <code>"longitude"</code> with the appropriate field names in your dataset that contain the latitude and longitude values.</li>
      </ul>
    </li>
    </ol>

    <p>The what3words address is stored as a string in the new field. In case the conversion fails due to invalid coordinates, a <code>NULL</code> value will be returned.</p>

    <h4>Example usage</h4>
    <ul>
      <li><code>convert_to_3wa(51.521251, -0.203586)</code> will return the corresponding what3words address for those coordinates.</li>
    </ul>

    <p>If you encounter errors during conversion, check if the API key is correctly set and ensure that the coordinates are valid.</p>
    """
    try:
        w3w = get_w3w_api()
        result = w3w.convertTo3wa(lat, lon)
        return result['words']
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
