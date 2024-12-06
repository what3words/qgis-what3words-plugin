import os
from qgis.core import (Qgis, QgsVectorLayer, QgsField, QgsProject, 
                       QgsWkbTypes, QgsFeature, QgsGeometry, QgsSymbolLayer,
                       QgsPointXY, QgsMarkerSymbol, QgsSvgMarkerSymbolLayer, QgsProperty)
from PyQt5.QtCore import QVariant
from qgis.utils import iface 
import time

class W3WPointLayerManager:
    """
    Manages a point layer for what3words locations in QGIS.

    This singleton class provides methods to create a point layer, check if it exists,
    and add point features to it. The point layer is used to display what3words locations
    on a QGIS map.

    Methods:
        getInstance(): Returns the singleton instance of the class.
        createPointLayer(): Creates a new point layer for what3words locations.
        layerExists(): Checks if the point layer exists in the project.
        addPointFeature(point_data, clicked_point=None): Adds a point feature to the layer.
    """
    _instance = None  # Singleton instance

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = W3WPointLayerManager()
        return cls._instance

    def __init__(self):
        """
        Initializes the W3WPointLayerManager class.
        Sets the point_layer attribute to None.
        """
        self.point_layer = None

    def createPointLayer(self):
        """
        Creates a new W3W point layer and adds it to the project with the same visible name.
        """
        # Use the same visible name for all layers
        visible_name = "what3words Points"

        # Use a unique internal name to prevent conflicts
        unique_id = int(time.time() * 1000)  # Use timestamp in milliseconds
        internal_name = f"{visible_name} {unique_id}"

        # Create a new memory layer for W3W points
        point_layer = QgsVectorLayer("Point?crs=EPSG:4326", internal_name, "memory")
        provider = point_layer.dataProvider()

        # Add attributes for the W3W point
        provider.addAttributes([
            QgsField("what3words", QVariant.String),
            QgsField("lat", QVariant.Double),
            QgsField("lng", QVariant.Double),
            QgsField("nearestPlace", QVariant.String),
            QgsField("country", QVariant.String),
            QgsField("language", QVariant.String)
        ])
        point_layer.updateFields()

        # Apply SVG marker style
        svg_path = os.path.join(os.path.dirname(__file__), "icons", "w3w_circle.svg")
        if os.path.exists(svg_path):
            svg_layer = QgsSvgMarkerSymbolLayer(svg_path)
            default_size = 4
            svg_layer.setSize(default_size)

            # Create a marker symbol and set the SVG layer
            symbol = QgsMarkerSymbol()
            symbol.changeSymbolLayer(0, svg_layer)

            # Apply the symbol to the point layer renderer
            point_layer.renderer().setSymbol(symbol)
            point_layer.triggerRepaint()

        # Add the new layer to the project with the same visible name
        point_layer.setName(visible_name)
        QgsProject.instance().addMapLayer(point_layer)

        self.point_layer = point_layer
        return self.point_layer

    def layerExists(self):
        """Check if the point layer exists in the project."""
        # Ensure the layer is defined and still part of the project
        return self.point_layer is not None and self.point_layer in QgsProject.instance().mapLayers().values()
    
    def addPointFeature(self, point_data, clicked_point=None):
        """
        Adds a W3W point feature to the layer.
        Uses `clicked_point` if provided, otherwise uses W3W API coordinates.
        """
        # Ensure 'words' is present in the response
        if 'words' not in point_data:
            return

        what3words = point_data['words']

        # Use clicked point's geometry if provided, otherwise use API coordinates
        if clicked_point:
            lat = clicked_point.y()
            lng = clicked_point.x()
        else:
            coordinates = point_data['coordinates']
            lat = coordinates['lat']
            lng = coordinates['lng']

        # Create the point geometry
        point = QgsPointXY(lng, lat)

        # Ensure the point layer exists
        if self.point_layer is None or not QgsProject.instance().mapLayersByName(self.point_layer.name()):
            self.createPointLayer()

        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPointXY(point))

        # Set attributes for the W3W point
        feature.setAttributes([
            what3words,
            lat,  # Use the lat from clicked_point or W3W API
            lng,  # Use the lng from clicked_point or W3W API
            point_data.get('nearestPlace', ''),
            point_data.get('country', ''),
            point_data.get('language', ''),
        ])

        # Add the feature to the layer
        self.point_layer.dataProvider().addFeatures([feature])
        self.point_layer.updateExtents()
        self.point_layer.triggerRepaint()
