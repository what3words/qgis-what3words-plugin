# -*- coding: utf-8 -*-
#
# (c) 2024 what3words
# This code is licensed under the GPL 2.0 license.
#

from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
                       QgsPoint, QgsLineSymbol, QgsSingleSymbolRenderer, QgsMapLayer)
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting
from what3words.w3w import what3words


class W3WGridManager:
    
    epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

    def __init__(self, canvas):
        self.canvas = canvas
        apiKey = pluginSetting("apiKey")
        self.w3w = what3words(apikey=apiKey)
        self.grid_layer = None  # Store reference to the grid layer
        self.grid_enabled = False  # Track whether grid is enabled

    def enableGrid(self, enable=True):
        """
        Enables or disables the automatic fetching of the W3W grid based on map movement.
        If the grid is disabled, the layer is removed.
        """
        self.grid_enabled = enable

        if enable:
            iface.mapCanvas().extentsChanged.connect(self.fetchAndDrawW3WGrid)
            self.fetchAndDrawW3WGrid()
        else:
            iface.mapCanvas().extentsChanged.disconnect(self.fetchAndDrawW3WGrid)
            self.removeGridLayer()

    def fetchAndDrawW3WGrid(self):
        """
        Fetches the What3words grid for the current map extent and draws it on the map.
        """
        if not self.grid_enabled:
            return

        # Get the current map extent and zoom level
        extent = self.canvas.extent()
        zoom_level = self.getZoomLevel()

        if zoom_level < 17 or zoom_level > 25:
            iface.messageBar().pushMessage("what3words", 
                "Zoom level must be between 17 and 25 to display the grid.", 
                level=Qgis.Warning, duration=3)
            return

        canvasCrs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(canvasCrs, self.epsg4326, QgsProject.instance())
        bottom_left = transform.transform(extent.xMinimum(), extent.yMinimum())
        top_right = transform.transform(extent.xMaximum(), extent.yMaximum())

        bounding_box = f"{bottom_left.y()},{bottom_left.x()},{top_right.y()},{top_right.x()}"

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            grid_data = self.w3w.getGridSection(bounding_box)

            self.ensureGridLayer()

            pr = self.grid_layer.dataProvider()
            self.grid_layer.startEditing()
            pr.deleteFeatures([f.id() for f in self.grid_layer.getFeatures()])
            self.grid_layer.commitChanges()

            for line in grid_data['lines']:
                point1 = QgsPoint(line['start']['lng'], line['start']['lat'])
                point2 = QgsPoint(line['end']['lng'], line['end']['lat'])
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline([point1, point2]))
                pr.addFeature(feature)

            self.grid_layer.updateExtents()
            self.applyGridSymbology()

        except Exception as e:
            iface.messageBar().pushMessage("what3words", 
                f"Error fetching grid: {str(e)}", level=Qgis.Critical, duration=5)
        finally:
            QApplication.restoreOverrideCursor()

    def removeGridLayer(self):
        """
        Safely removes the grid layer from the project, if it exists.
        """
        if self.grid_layer:
            layers = QgsProject.instance().mapLayersByName(self.grid_layer.name())
            if layers:
                QgsProject.instance().removeMapLayer(layers[0])
            self.grid_layer = None

    def ensureGridLayer(self):
        """
        Ensures that the grid layer exists. If it doesn't, this method recreates it.
        """
        if not self.grid_layer or not QgsProject.instance().mapLayersByName(self.grid_layer.name()):
            self.grid_layer = QgsVectorLayer("LineString", "W3W Grid", "memory")
            QgsProject.instance().addMapLayer(self.grid_layer)

    def applyGridSymbology(self):
        """
        Applies symbology to the W3W grid layer based on whether a satellite or vector map is active.
        """
        satellite_keywords = ['satellite', 'google', 'imagery', 'arcgis satellite', 'bing aerial', 'google satellite']
        is_satellite_map = False

        layers = list(QgsProject.instance().mapLayers().values())
        for layer in layers:
            if layer.type() == QgsMapLayer.RasterLayer or 'XYZ' in layer.providerType():
                layer_name = layer.name().lower()
                for keyword in satellite_keywords:
                    if keyword in layer_name:
                        is_satellite_map = True
                        break

        if is_satellite_map:
            color = '#ffffff'
            opacity = 0.16
        else:
            color = '#000000'
            opacity = 0.24

        symbol = QgsLineSymbol.createSimple({
            'color': color,
            'width': '0.5'
        })
        symbol.setOpacity(opacity)
        renderer = QgsSingleSymbolRenderer(symbol)
        self.grid_layer.setRenderer(renderer)
        self.grid_layer.triggerRepaint()

    def getZoomLevel(self):
        """
        Returns the current zoom level based on the map extent and canvas size.
        """
        extent = self.canvas.extent()
        width = extent.width()
        canvas_width = self.canvas.mapSettings().outputSize().width()
        zoom_level = 25 - (width / canvas_width) * 8
        return int(zoom_level)
