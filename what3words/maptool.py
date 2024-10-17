import os
from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsPointXY, QgsField)
from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting
from what3words.w3w import what3words
from what3words.shared_layer_point import W3WPointLayerManager


class W3WMapTool(QgsMapTool):

    epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)
        apiKey = pluginSetting("apiKey")
        self.w3w = what3words(apikey=apiKey)
        self.point_layer_manager = W3WPointLayerManager.getInstance()

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

            # Log or print the API response for debugging
            if 'words' not in w3w_info or 'coordinates' not in w3w_info:
                raise ValueError("Missing 'words' or 'coordinates' in API response")
                
            return w3w_info, pt4326  # Return both W3W info and transformed point

        except Exception as ex:
            print(f"Error calling what3words API: {str(ex)}")
            raise  # Re-raise the exception after logging it
        finally:
            QApplication.restoreOverrideCursor()


    def canvasReleaseEvent(self, e):
        """
        Triggered when the user clicks on the map. This will convert the clicked point
        to a what3words address and display it to the user, as well as drawing the point.
        """
        pt = self.toMapCoordinates(e.pos())
        try:
            w3w_info, pt4326 = self.toW3W(pt)  # Get both W3W info and transformed point

            # Check if 'coordinates' and 'words' exist in the response
            if not w3w_info or 'coordinates' not in w3w_info or 'words' not in w3w_info:
                iface.messageBar().pushMessage(
                    "what3words", 
                    "Invalid what3words data: Missing coordinates or words", 
                    level=Qgis.Warning, duration=5
                )
                return

            # Add the what3words point to the shared layer, using the transformed point
            self.point_layer_manager.addPointFeature(w3w_info, clicked_point=pt4326)

            # Notify user and copy W3W address to clipboard
            iface.messageBar().pushMessage(
                "what3words", 
                f"The what3words address: '{w3w_info['words']}' has been copied to the clipboard", 
                level=Qgis.Info, duration=6
            )
            clipboard = QApplication.clipboard()
            clipboard.setText(w3w_info['words'])

        except Exception as ex:
            iface.messageBar().pushMessage(
                "what3words", 
                f"Error processing what3words point: {str(ex)}", 
                level=Qgis.Warning, duration=5
            )
