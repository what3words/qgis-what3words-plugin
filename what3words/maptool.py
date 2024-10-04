# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

from qgis.core import (Qgis, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject,
                       QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint)
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
            
    def fetchAndDrawW3WGrid(self):
        """
        Fetches the What3words grid for the current map extent and draws it on the map.
        Only draws the grid for zoom levels between 17 and 21.
        """
        # Get the current map extent and zoom level
        canvas = iface.mapCanvas()
        extent = canvas.extent()
        zoom_level = self.getZoomLevel()

        if zoom_level < 17 or zoom_level > 21:
            iface.messageBar().pushMessage("what3words", 
                "Zoom level must be between 17 and 21 to display the grid.", 
                level=Qgis.Warning, duration=3)
            return

        # Convert the extent to a bounding box string for the What3words API
        bounding_box = f"{extent.yMinimum()},{extent.xMinimum()},{extent.yMaximum()},{extent.xMaximum()}"

        # Fetch the What3words grid for the current extent
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            grid_data = self.w3w.getGridSection(bounding_box)

            if self.grid_layer:
                QgsProject.instance().removeMapLayer(self.grid_layer)

            # Create a new memory layer for the grid lines
            self.grid_layer = QgsVectorLayer("LineString", "W3W Grid", "memory")
            pr = self.grid_layer.dataProvider()

            # Loop through the grid lines and add them as features to the layer
            for line in grid_data['lines']:
                point1 = QgsPoint(line['start']['lng'], line['start']['lat'])
                point2 = QgsPoint(line['end']['lng'], line['end']['lat'])
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline([point1, point2]))
                pr.addFeature(feature)

            self.grid_layer.updateExtents()
            QgsProject.instance().addMapLayer(self.grid_layer)

        except Exception as e:
            iface.messageBar().pushMessage("what3words", 
                f"Error fetching grid: {str(e)}", level=Qgis.Critical, duration=5)
        finally:
            QApplication.restoreOverrideCursor()

    def getZoomLevel(self):
        """
        Returns the current zoom level based on the map extent and canvas size.
        """
        canvas = iface.mapCanvas()
        extent = canvas.extent()
        width = extent.width()
        canvas_width = canvas.mapSettings().outputSize().width()

        # Approximate zoom level calculation (not perfectly accurate, but works for this purpose)
        zoom_level = int(20 - (width / canvas_width))
        return zoom_level
