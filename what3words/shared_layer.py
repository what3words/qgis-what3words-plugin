from qgis.core import Qgis, QgsVectorLayer, QgsField, QgsProject, QgsWkbTypes, QgsFeature, QgsGeometry, QgsPointXY
from PyQt5.QtCore import QVariant
from qgis.utils import iface

class W3WSquareLayerManager:
    _instance = None  # Singleton instance

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = W3WSquareLayerManager()
        return cls._instance

    def __init__(self):
        self.square_layer = None

    def createSquareLayer(self):
        """
        Creates the square layer if it does not exist.
        """
        if self.square_layer is None:
            # Create the memory layer for W3W squares
            self.square_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "W3W Square", "memory")
            provider = self.square_layer.dataProvider()

            # Add attributes for the W3W square
            provider.addAttributes([
                QgsField("what3words", QVariant.String),
                QgsField("lat", QVariant.Double),
                QgsField("lng", QVariant.Double),
                QgsField("nearestPlace", QVariant.String),
                QgsField("country", QVariant.String),
                QgsField("language", QVariant.String)
            ])
            self.square_layer.updateFields()

            # Add the layer to the project
            QgsProject.instance().addMapLayer(self.square_layer)

    def checkForDuplicate(self, what3words):
        """
        Checks if the given what3words already exists in the layer.
        :param what3words: The what3words address to check for duplicates.
        :return: True if the address exists, False otherwise.
        """
        if not self.square_layer:
            return False

        # Check each feature in the layer to see if the what3words already exists
        for feature in self.square_layer.getFeatures():
            if feature['what3words'] == what3words:
                return True
        return False

    def addSquareFeature(self, square_data):
        """
        Adds a W3W square feature to the layer, but first checks for duplicates.
        """
        if 'square' not in square_data or 'words' not in square_data:
            iface.messageBar().pushMessage("what3words", "Invalid W3W data: Missing square or words", level=Qgis.Warning, duration=5)
            return

        what3words = square_data['words']
        
        # Check for duplicates before adding
        if self.checkForDuplicate(what3words):
            iface.messageBar().pushMessage("what3words", f"Duplicate W3W square: '{what3words}' already exists in the layer.", level=Qgis.Warning, duration=5)
            return  # Do not add a duplicate

        square = square_data['square']
        if 'southwest' not in square or 'northeast' not in square:
            iface.messageBar().pushMessage("what3words", "Invalid W3W square data: Missing southwest or northeast coordinates", level=Qgis.Warning, duration=5)
            return

        if 'coordinates' not in square_data:
            southwest = square['southwest']
            northeast = square['northeast']

            # Calculate center (midpoint of southwest and northeast)
            center_lat = (southwest['lat'] + northeast['lat']) / 2
            center_lng = (southwest['lng'] + northeast['lng']) / 2

            coordinates = {'lat': center_lat, 'lng': center_lng}
        else:
            coordinates = square_data['coordinates']

        bottom_left = QgsPointXY(square['southwest']['lng'], square['southwest']['lat'])
        top_right = QgsPointXY(square['northeast']['lng'], square['northeast']['lat'])
        top_left = QgsPointXY(square['southwest']['lng'], square['northeast']['lat'])
        bottom_right = QgsPointXY(square['northeast']['lng'], square['southwest']['lat'])

        points = [bottom_left, top_left, top_right, bottom_right, bottom_left]
        polygon = QgsGeometry.fromPolygonXY([points])

        # Ensure the square layer exists
        if self.square_layer is None or not QgsProject.instance().mapLayersByName(self.square_layer.name()):
            self.createSquareLayer()

        feature = QgsFeature()
        feature.setGeometry(polygon)

        # Set attributes for the W3W square
        feature.setAttributes([
            square_data['words'],
            coordinates['lat'],
            coordinates['lng'],
            square_data.get('nearestPlace', ''),
            square_data.get('country', ''),
            square_data.get('language', '')
        ])

        # Add the feature and refresh the layer
        self.square_layer.dataProvider().addFeatures([feature])
        self.square_layer.updateExtents()
        self.square_layer.triggerRepaint()
