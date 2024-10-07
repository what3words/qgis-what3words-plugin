# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

from qgis.core import (Qgis, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject,
                       QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint,
                       QgsLineSymbol, QgsSingleSymbolRenderer, QgsRendererCategory, 
                       QgsMapLayer)

from qgis.gui import QgsMapTool, QgsMessageBar
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting

from what3words.w3w import what3words
from what3words.w3w import what3words


class W3WMapTool(QgsMapTool):

    epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.setCursor(Qt.CrossCursor)
        apiKey = pluginSetting("apiKey")
        self.w3w = what3words(apikey=apiKey)
        self.grid_layer = None  # Store reference to the grid layer
        self.grid_enabled = False  # New flag to track whether grid is enabled

    def toW3W(self, pt):
        canvas = iface.mapCanvas()
        canvasCrs = canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(canvasCrs, self.epsg4326, QgsProject.instance())
        pt4326 = transform.transform(pt.x(), pt.y())

        apiKey = pluginSetting("apiKey")
        addressLanguage = pluginSetting("addressLanguage")
        self.w3w = what3words(apikey=apiKey,addressLanguage=addressLanguage)
        
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            w3wCoords = self.w3w.convertTo3wa(pt4326.y(), pt4326.x())["words"]
        except Exception as e :
            w3wCoords = str(e)
        finally:
            QApplication.restoreOverrideCursor()

        return w3wCoords

    def canvasReleaseEvent(self, e):
        pt = self.toMapCoordinates(e.pos())
        w3wCoord = self.toW3W(pt)
        if w3wCoord:
            iface.messageBar().pushMessage("what3words", 
                "The 3 word address: '{}' has been copied to the clipboard".format(w3wCoord), 
                level=Qgis.Info, duration=6)
            clipboard = QApplication.clipboard()
            clipboard.setText(w3wCoord)
        else:
            iface.messageBar().pushMessage("what3words", 
                "Could not convert the selected point to a 3 word address",
                level=Qgis.Warning, duration=3)

    def enableGrid(self, enable=True):
        """
        Enables or disables the automatic fetching of the W3W grid based on map movement.
        """
        self.grid_enabled = enable

        if enable:
            iface.mapCanvas().extentsChanged.connect(self.fetchAndDrawW3WGrid)  # Connect signal
            self.fetchAndDrawW3WGrid()  # Initial draw
        else:
            iface.mapCanvas().extentsChanged.disconnect(self.fetchAndDrawW3WGrid)  # Disconnect signal
            # Check if the grid_layer still exists in the project before attempting to remove it
            if self.grid_layer and QgsProject.instance().mapLayersByName(self.grid_layer.name()):
                QgsProject.instance().removeMapLayer(self.grid_layer)
            self.grid_layer = None  # Ensure the reference is cleared

    def fetchAndDrawW3WGrid(self):
        """
        Fetches the What3words grid for the current map extent and draws it on the map.
        Sets different symbology based on whether a satellite (raster) or vector map is active.
        Always recreates the grid layer if it has been deleted or removed.
        Only draws the grid for zoom levels between 17 and 25 if grid is enabled.
        """
        if not self.grid_enabled:
            return

        # Get the current map extent and zoom level
        canvas = iface.mapCanvas()
        extent = canvas.extent()
        zoom_level = self.getZoomLevel()

        if zoom_level < 17 or zoom_level > 25:
            iface.messageBar().pushMessage("what3words", 
                "Zoom level must be between 17 and 25 to display the grid.", 
                level=Qgis.Warning, duration=3)
            return

        # Get the map canvas CRS (which might not be WGS84)
        canvasCrs = canvas.mapSettings().destinationCrs()

        # Create a transform object to convert the coordinates to WGS84 (EPSG:4326)
        transform = QgsCoordinateTransform(canvasCrs, self.epsg4326, QgsProject.instance())

        # Transform the extent coordinates to EPSG:4326 (WGS84)
        bottom_left = transform.transform(extent.xMinimum(), extent.yMinimum())
        top_right = transform.transform(extent.xMaximum(), extent.yMaximum())

        # Create the bounding box string in WGS84 for the API call
        bounding_box = f"{bottom_left.y()},{bottom_left.x()},{top_right.y()},{top_right.x()}"

        # Fetch the What3words grid for the current extent
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            grid_data = self.w3w.getGridSection(bounding_box)

            # Ensure that the grid layer exists or recreate it if needed
            self.ensureGridLayer()

            # Get the data provider for the grid layer
            pr = self.grid_layer.dataProvider()

            # Clear any existing features in the layer (to avoid duplicates)
            self.grid_layer.startEditing()
            pr.deleteFeatures([f.id() for f in self.grid_layer.getFeatures()])
            self.grid_layer.commitChanges()

            # Loop through the grid lines and add them as features to the layer
            for line in grid_data['lines']:
                point1 = QgsPoint(line['start']['lng'], line['start']['lat'])  # Points already in WGS84
                point2 = QgsPoint(line['end']['lng'], line['end']['lat'])      # Points already in WGS84
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline([point1, point2]))
                pr.addFeature(feature)

            self.grid_layer.updateExtents()

            # Apply symbology based on map type
            self.applyGridSymbology()

        except Exception as e:
            iface.messageBar().pushMessage("what3words", 
                f"Error fetching grid: {str(e)}", level=Qgis.Critical, duration=5)
        finally:
            QApplication.restoreOverrideCursor()


    def enableGrid(self, enable=True):
        """
        Enables or disables the automatic fetching of the W3W grid based on map movement.
        If the grid is disabled, the layer is removed.
        """
        self.grid_enabled = enable

        if enable:
            iface.mapCanvas().extentsChanged.connect(self.fetchAndDrawW3WGrid)  # Connect signal
            self.fetchAndDrawW3WGrid()  # Initial draw
        else:
            iface.mapCanvas().extentsChanged.disconnect(self.fetchAndDrawW3WGrid)  # Disconnect signal
            self.removeGridLayer()  # Safely remove the layer

    def removeGridLayer(self):
        """
        Safely removes the grid layer from the project, if it exists.
        """
        if self.grid_layer:
            # Check if the layer still exists in the project
            layers = QgsProject.instance().mapLayersByName(self.grid_layer.name())
            if layers:
                QgsProject.instance().removeMapLayer(layers[0])
            self.grid_layer = None  # Clear the reference to avoid using a deleted object


    def ensureGridLayer(self):
        """
        Ensures that the grid layer exists.
        If the grid layer has been deleted, this method recreates it.
        """
        # Check if the layer still exists in the project
        if not self.grid_layer or not QgsProject.instance().mapLayersByName(self.grid_layer.name()):
            # The layer doesn't exist anymore or is invalid, recreate it
            self.grid_layer = QgsVectorLayer("LineString", "W3W Grid", "memory")
            QgsProject.instance().addMapLayer(self.grid_layer)
        else:
            # If the layer exists but has been deleted, reset it
            layers = QgsProject.instance().mapLayersByName(self.grid_layer.name())
            if not layers:
                # Recreate the layer if it's not valid anymore
                self.grid_layer = QgsVectorLayer("LineString", "W3W Grid", "memory")
                QgsProject.instance().addMapLayer(self.grid_layer)

    def applyGridSymbology(self):
        """
        Applies symbology to the W3W grid layer based on the type of map (vector or satellite).
        For vector maps: black lines (#000000) with 24% opacity.
        For satellite maps: white lines (#ffffff) with 16% opacity.
        """
        # List of known satellite basemap keywords
        satellite_keywords = ['satellite', 'google', 'imagery', 'arcgis satellite', 'bing aerial', 'google satellite']

        # Default to vector map
        is_satellite_map = False

        # Get all layers in the project
        layers = list(QgsProject.instance().mapLayers().values())

        # Iterate over all layers and find the bottom-most raster or XYZ tile layer
        for layer in layers:
            # Check if the layer is a raster or XYZ tile layer
            if layer.type() == QgsMapLayer.RasterLayer or 'XYZ' in layer.providerType():
                # Check if the layer name contains any satellite keywords
                layer_name = layer.name().lower()

                for keyword in satellite_keywords:
                    if keyword in layer_name:
                        is_satellite_map = True
                        break

        # Set symbology based on the type of map
        if is_satellite_map:
            # Satellite map: White lines with 16% opacity
            color = '#ffffff'
            opacity = 0.16
        else:
            # Vector map: Black lines with 24% opacity
            color = '#000000'
            opacity = 0.24

        # Create a simple line symbol with the correct color and opacity
        symbol = QgsLineSymbol.createSimple({
            'color': color,
            'width': '0.5'
        })
        
        # Set the opacity for the symbol
        symbol.setOpacity(opacity)

        # Apply a single symbol renderer to the grid layer
        renderer = QgsSingleSymbolRenderer(symbol)
        self.grid_layer.setRenderer(renderer)
        self.grid_layer.triggerRepaint()

    def getZoomLevel(self):
        """
        Returns the current zoom level based on the map extent and canvas size.
        """
        canvas = iface.mapCanvas()
        extent = canvas.extent()
        width = extent.width()
        canvas_width = canvas.mapSettings().outputSize().width()

        # Approximate zoom level calculation (not perfectly accurate, but works for this purpose)
        # Adjust the calculation to ensure zoom levels fit between 17 and 25.
        zoom_level = 25 - (width / canvas_width) * 8  # Adjust zoom level scale
        return int(zoom_level)
    