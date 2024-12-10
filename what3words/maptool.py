import os
from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsPointXY)
from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from PyQt5.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface
from what3words.w3w import GeoCodeException
from what3words.shared_layer_point import W3WPointLayerManager
from what3words.utils import get_w3w_instance


class W3WMapTool(QgsMapTool):
    w3wAddressCaptured = pyqtSignal(QgsPointXY)
    w3wAddressCapturedForMapsite = pyqtSignal(str)
    epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

    def __init__(self, canvas, coordDialog):
        super().__init__(canvas)
        self.canvas = canvas
        self.coordDialog = coordDialog  # Pass coorddialog instance to access the checkbox
        self.setCursor(Qt.CrossCursor)
        self.point_layer_manager = W3WPointLayerManager.getInstance()

    def toW3W(self, pt):
        """
        Converts the given point to a what3words address using the API.
        """
        canvas = iface.mapCanvas()
        canvasCrs = canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(canvasCrs, self.epsg4326, QgsProject.instance())
        pt4326 = transform.transform(pt.x(), pt.y())

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.w3w = get_w3w_instance() 
            w3w_info = self.w3w.convertTo3wa(pt4326.y(), pt4326.x())

            # Validate the API response
            if 'words' not in w3w_info or 'coordinates' not in w3w_info:
                raise GeoCodeException("Invalid API response: missing 'words' or 'coordinates'.")


            return w3w_info, pt4326
        except GeoCodeException as e:
            # Show the API error to the user
            iface.messageBar().pushMessage("what3words", str(e), level=Qgis.Warning, duration=2)
            return None, pt4326  # Return None for w3w_info and the transformed point
        finally:
            QApplication.restoreOverrideCursor()

    def canvasReleaseEvent(self, e):
        """
        Triggered when the user clicks on the map. This converts the clicked point
        to a what3words address, adds a marker, updates the table, and copies the address to the clipboard.
        """
        pt = self.toMapCoordinates(e.pos())
        self.w3wAddressCaptured.emit(pt)

        try:
            w3w_info, pt4326 = self.toW3W(pt)  # Get W3W info and transformed point
            if not w3w_info:
                return

            # Emit the new signal for mapsite with the 3WA
            self.w3wAddressCapturedForMapsite.emit(w3w_info['words'])

            # Add the marker on the map at the selected point
            self.coordDialog.addMarker(pt)

            # Add the W3W address to the coord dialog's table
            self.coordDialog.addRowToTable(
                what3words=w3w_info['words'],
                lat=pt4326.y(),
                lon=pt4326.x(),
                nearest_place=w3w_info.get('nearestPlace', ''),
                country=w3w_info.get('country', ''),
                language=w3w_info.get('language', '')
            )
        except GeoCodeException as e:
            iface.messageBar().pushMessage("what3words", str(e), level=Qgis.Warning, duration=2)