import os
from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsPointXY, QgsField)
from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting
from what3words.shared_layer import W3WSquareLayerManager
from what3words.w3w import what3words


class W3WMapTool(QgsMapTool):

    epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)
        apiKey = pluginSetting("apiKey")
        self.w3w = what3words(apikey=apiKey)
        self.square_layer_manager = W3WSquareLayerManager.getInstance()  # Use singleton instance
        
    def toW3W(self, pt):
        """
        Converts the given point to a what3words address using the API.
        """
        canvas = iface.mapCanvas()
        canvasCrs = canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(canvasCrs, self.epsg4326, QgsProject.instance())
        pt4326 = transform.transform(pt.x(), pt.y())

        apiKey = pluginSetting("apiKey")
        addressLanguage = pluginSetting("addressLanguage")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)
        
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            w3w_info = self.w3w.convertTo3wa(pt4326.y(), pt4326.x())
        finally:
            QApplication.restoreOverrideCursor()

        return w3w_info

    def canvasReleaseEvent(self, e):
        """
        Triggered when the user clicks on the map. This will convert the clicked point
        to a what3words address and display it to the user, as well as drawing the square.
        """
        pt = self.toMapCoordinates(e.pos())
        w3w_info = self.toW3W(pt)
        if w3w_info:
            iface.messageBar().pushMessage(
                "what3words", 
                "The what3words address: '{}' has been copied to the clipboard".format(w3w_info['words']), 
                level=Qgis.Info, duration=6
            )
            clipboard = QApplication.clipboard()
            clipboard.setText(w3w_info['words'])

            # Add the W3W square to the shared layer
            self.square_layer_manager.addSquareFeature(w3w_info)
        else:
            iface.messageBar().pushMessage(
                "what3words", 
                "Could not convert the selected point to a what3words address",
                level=Qgis.Warning, duration=3
            )

