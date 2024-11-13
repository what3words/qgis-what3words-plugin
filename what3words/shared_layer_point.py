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
        if not self.layerExists():
            # Create the memory layer for W3W points
            self.point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "what3words Points", "memory")
            provider = self.point_layer.dataProvider()

            # Add attributes for the W3W point
            provider.addAttributes([
                QgsField("w3w_address", QVariant.String),
                QgsField("lat", QVariant.Double),
                QgsField("lng", QVariant.Double),
                QgsField("nearestPlace", QVariant.String),
                QgsField("country", QVariant.String),
                QgsField("language", QVariant.String),
                QgsField("label", QVariant.String)
            ])
            self.point_layer.updateFields()

            # Apply SVG marker style
            svg_path = os.path.join(os.path.dirname(__file__), "icons", "w3w_circle.svg")
            if os.path.exists(svg_path):
                svg_layer = QgsSvgMarkerSymbolLayer(svg_path)
                
                # Set a default size for zoom levels lower than 17
                default_size = 4
                svg_layer.setSize(default_size)

                # Set the size dynamically based on the zoom level
                # zoom_level_expression = """
                #     case
                #     when @map_scale >= 2000 then {default_size}  -- Keep the default size if scale is above 2000
                #     else 8 * (500 / @map_scale)  -- Dynamically scale for zoom levels lower than 2000
                #     end
                #     """.format(default_size=default_size)                
                # size_property = QgsProperty.fromExpression(zoom_level_expression)

                # # Apply the data-defined size property
                # svg_layer.setDataDefinedProperty(QgsSymbolLayer.PropertySize, size_property)

                # Create a marker symbol and set the SVG layer
                symbol = QgsMarkerSymbol()
                symbol.changeSymbolLayer(0, svg_layer)

                # Apply the symbol to the point layer renderer
                self.point_layer.renderer().setSymbol(symbol)
                self.point_layer.triggerRepaint()

            # Add the layer to the project
            QgsProject.instance().addMapLayer(self.point_layer)

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

        w3w_address = point_data['words']

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
            w3w_address,
            lat,  # Use the lat from clicked_point or W3W API
            lng,  # Use the lng from clicked_point or W3W API
            point_data.get('nearestPlace', ''),
            point_data.get('country', ''),
            point_data.get('language', ''),
            point_data.get('label', ''),
        ])

        # Add the feature to the layer
        self.point_layer.dataProvider().addFeatures([feature])
        self.point_layer.updateExtents()
        self.point_layer.triggerRepaint()
