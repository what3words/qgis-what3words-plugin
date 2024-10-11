import os
from qgis.core import (Qgis, QgsVectorLayer, QgsField, QgsProject, 
                       QgsWkbTypes, QgsFeature, QgsGeometry, QgsSymbolLayer,
                       QgsPointXY, QgsMarkerSymbol, QgsSvgMarkerSymbolLayer, QgsProperty)
from PyQt5.QtCore import QVariant
from qgis.utils import iface

class W3WPointLayerManager:
    _instance = None  # Singleton instance

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = W3WPointLayerManager()
        return cls._instance

    def __init__(self):
        self.point_layer = None

    def createPointLayer(self):
        """
        Creates the point layer if it does not exist.
        """
        if self.point_layer is None:
            # Create the memory layer for W3W points
            self.point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "W3W Points", "memory")
            provider = self.point_layer.dataProvider()

            # Add attributes for the W3W point
            provider.addAttributes([
                QgsField("w3w_address", QVariant.String),
                QgsField("lat", QVariant.Double),
                QgsField("lng", QVariant.Double),
                QgsField("nearestPlace", QVariant.String),
                QgsField("country", QVariant.String)
            ])
            self.point_layer.updateFields()

            # Apply SVG marker style
            svg_path = os.path.join(os.path.dirname(__file__), "icons", "w3w.svg")
            if os.path.exists(svg_path):
                svg_layer = QgsSvgMarkerSymbolLayer(svg_path)
                
                # Set a default size for zoom levels lower than 17
                default_size = 4
                svg_layer.setSize(default_size)

                # Set the size dynamically based on the zoom level
                zoom_level_expression = """
                    case
                    when @map_scale >= 2000 then {default_size}  -- Keep the default size if scale is above 2000
                    else 19 * (500 / @map_scale)  -- Dynamically scale for zoom levels lower than 2000
                    end
                    """.format(default_size=default_size)                
                size_property = QgsProperty.fromExpression(zoom_level_expression)

                # Apply the data-defined size property
                svg_layer.setDataDefinedProperty(QgsSymbolLayer.PropertySize, size_property)

                # Create a marker symbol and set the SVG layer
                symbol = QgsMarkerSymbol()
                symbol.changeSymbolLayer(0, svg_layer)

                # Apply the symbol to the point layer renderer
                self.point_layer.renderer().setSymbol(symbol)
                self.point_layer.triggerRepaint()

            # Add the layer to the project
            QgsProject.instance().addMapLayer(self.point_layer)

    def checkForDuplicate(self, w3w_address):
        """
        Checks if the given w3w_address already exists in the layer.
        :param w3w_address: The what3words address to check for duplicates.
        :return: True if the address exists, False otherwise.
        """
        if not self.point_layer:
            return False

        # Check each feature in the layer to see if the w3w_address already exists
        for feature in self.point_layer.getFeatures():
            if feature['w3w_address'] == w3w_address:
                return True
        return False

    def addPointFeature(self, point_data):
        """
        Adds a W3W point feature to the layer, but first checks for duplicates.
        """
        # Ensure both 'coordinates' and 'words' are present in the response
        if 'coordinates' not in point_data or 'words' not in point_data:
            iface.messageBar().pushMessage(
                "what3words", 
                "Invalid W3W data: Missing coordinates or words", 
                level=Qgis.Warning, duration=5
            )
            return

        w3w_address = point_data['words']

        # Check for duplicates before adding
        if self.checkForDuplicate(w3w_address):
            iface.messageBar().pushMessage(
                "what3words", 
                f"Duplicate W3W point: '{w3w_address}' already exists in the layer.", 
                level=Qgis.Warning, duration=5
            )
            return  # Do not add a duplicate

        # Use the exact coordinates from the API response
        coordinates = point_data['coordinates']
        lat = coordinates['lat']
        lng = coordinates['lng']

       # Create the point geometry using exact coordinates
        point = QgsPointXY(lng, lat)

        # Ensure the point layer exists
        if self.point_layer is None or not QgsProject.instance().mapLayersByName(self.point_layer.name()):
            self.createPointLayer()

        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPointXY(point))

        # Set attributes for the W3W point
        feature.setAttributes([
            w3w_address,
            coordinates['lat'],
            coordinates['lng'],
            point_data.get('nearestPlace', ''),
            point_data.get('country', '')
        ])

        # Add the feature to the layer
        self.point_layer.dataProvider().addFeatures([feature])
        self.point_layer.updateExtents()
        self.point_layer.triggerRepaint()
        
        # Notify user of successful addition
        iface.messageBar().pushMessage("what3words", f"Point added for '{w3w_address}'", level=Qgis.Success, duration=5)

