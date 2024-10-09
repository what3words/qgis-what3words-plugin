from builtins import str
# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

import os
from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsPointXY, QgsVectorLayer, QgsFeature,
                       QgsGeometry, QgsField)
from qgis.PyQt.QtCore import Qt, QStringListModel, QVariant
from qgis.PyQt.QtGui import QCursor, QPalette
from qgis.PyQt.QtWidgets import (QApplication, QDockWidget, QHBoxLayout, QLabel,
                                 QLineEdit, QWidget, QCompleter, QListView)
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting
from what3words.w3w import what3words


class W3WCoordInputDialog(QDockWidget):
    def __init__(self, canvas, parent):
        self.canvas = canvas
        self.square_layer = None  # Layer for drawing the w3w square
        self.zoom_level = 20  # Default zoom level set to 20
        QDockWidget.__init__(self, parent)
        self.setAllowedAreas(Qt.TopDockWidgetArea)
        self.initGui()

    def setApiKey(self, apikey):
        self.w3w = what3words(apikey=apikey)

    def setAddressLanguage(self, addressLanguage):
        self.w3w = what3words(addressLanguage=addressLanguage)

    def initGui(self):
        self.setWindowTitle("Zoom to what3words address")

        # Set up the UI
        self.label = QLabel('what3words address')
        self.coordBox = QLineEdit()

        # Auto-suggest functionality
        self.completer = QCompleter()
        self.completer.setPopup(QListView())  # Use a list view for better control of the styling
        self.completer.setCompletionMode(QCompleter.PopupCompletion)  # Show the popup
        self.completer.activated.connect(self.zoomToSelected)  # Zoom to selected suggestion
        self.coordBox.setCompleter(self.completer)
        self.coordBox.textChanged.connect(self.suggestW3W)

        # Layout
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.label)
        hlayout.addWidget(self.coordBox)
        dockWidgetContents = QWidget()
        dockWidgetContents.setLayout(hlayout)
        self.setWidget(dockWidgetContents)

        # Handle dark mode
        self.handleDarkMode()

    def handleDarkMode(self):
        """
        Adjusts the input box style and forces text color to be black.
        """
        palette = self.coordBox.palette()
        palette.setColor(QPalette.Text, Qt.black)  # Force text to be black
        palette.setColor(QPalette.Base, Qt.white)  # Set background to white
        self.coordBox.setPalette(palette)

    def suggestW3W(self, text):
        """
        Fetches suggestions based on the input text for autosuggest functionality.
        Trigger suggestions after at least the first letter of the 3rd word is entered.
        """
        if text.count('.') < 2 or len(text.split('.')[-1]) < 1:
            return  # Only suggest after second dot and at least 1 character in the 3rd word

        apiKey = pluginSetting("apiKey")
        addressLanguage = pluginSetting("addressLanguage")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)

        try:
            suggestions = self.w3w.autosuggest(text)
            # Limit to 3 suggestions and only show the what3words address
            suggestion_list = [suggestion['words'] for suggestion in suggestions['suggestions'][:3]]

            # Create a model for the completer with the what3words suggestions
            completer_model = QStringListModel(suggestion_list)
            self.completer.setModel(completer_model)
            self.completer.complete()  # Show the suggestions dropdown
        except Exception as e:
            iface.messageBar().pushMessage("what3words", 
                f"Error fetching suggestions: {str(e)}", level=Qgis.Warning, duration=5)

    def zoomToSelected(self, selected_text):
        """
        Zoom to the selected what3words address from the suggestions.
        """
        apiKey = pluginSetting("apiKey")
        addressLanguage = pluginSetting("addressLanguage")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)

        try:
            w3wCoord = str(selected_text).replace(" ", "")
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            json = self.w3w.convertToCoordinates(w3wCoord)

            # Check if required keys are present in the API response
            if 'coordinates' not in json or 'square' not in json or 'words' not in json:
                raise ValueError("Invalid API response: Missing required data.")

            lat = float(json["coordinates"]["lat"])
            lon = float(json["coordinates"]["lng"])
            square = json["square"]

            # Transform the center point to the canvas CRS
            canvasCrs = self.canvas.mapSettings().destinationCrs()
            epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
            transform4326 = QgsCoordinateTransform(epsg4326, canvasCrs, QgsProject.instance())
            center = transform4326.transform(lon, lat)

            # Zoom to the point with user-defined zoom level (zoom set to 20)
            self.canvas.setCenter(center)
            self.canvas.zoomScale(591657550.5 / (2 ** self.zoom_level))  # Zoom to level 20
            self.canvas.refresh()

            # Draw the what3words square on the map
            self.drawW3WSquare(json)

        except ValueError as ve:
            iface.messageBar().pushMessage("what3words", f"Value Error: {str(ve)}", level=Qgis.Warning, duration=5)
        except Exception as e:
            iface.messageBar().pushMessage("what3words", f"The Error is: {str(e)}", level=Qgis.Warning, duration=5)
        finally:
            QApplication.restoreOverrideCursor()

    def drawW3WSquare(self, json):
        """
        Draw the what3words square as a polygon on the map and add API info as attributes.
        """
        square = json["square"]

        # Check if 'square', 'coordinates', and 'words' exist in the API response
        if 'southwest' not in square or 'northeast' not in square:
            iface.messageBar().pushMessage("what3words", "Invalid API response: Missing square data.", level=Qgis.Critical, duration=5)
            return

        # Coordinates of the square
        southwest = square["southwest"]
        northeast = square["northeast"]

        # Create the polygon for the square
        bottom_left = QgsPointXY(southwest["lng"], southwest["lat"])
        top_right = QgsPointXY(northeast["lng"], northeast["lat"])
        top_left = QgsPointXY(southwest["lng"], northeast["lat"])
        bottom_right = QgsPointXY(northeast["lng"], southwest["lat"])

        points = [bottom_left, top_left, top_right, bottom_right, bottom_left]
        polygon = QgsGeometry.fromPolygonXY([points])

        # Create a memory layer for the square (if not already created)
        if not self.square_layer:
            self.square_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "W3W Square", "memory")
            provider = self.square_layer.dataProvider()

            # Define attributes (columns) for the layer
            provider.addAttributes([
                QgsField("words", QVariant.String),
                QgsField("nearestPlace", QVariant.String),
                QgsField("country", QVariant.String),
                QgsField("lat", QVariant.Double),
                QgsField("lng", QVariant.Double)
            ])
            self.square_layer.updateFields()  # Update layer's fields

            QgsProject.instance().addMapLayer(self.square_layer)

        # Add the square feature with attributes
        feature = QgsFeature()
        feature.setGeometry(polygon)

        # Set attributes from the API response
        feature.setAttributes([
            json.get('words', ''),
            json.get('nearestPlace', ''),
            json.get('country', ''),
            json['coordinates']['lat'],
            json['coordinates']['lng']
        ])

        self.square_layer.dataProvider().addFeatures([feature])
        self.square_layer.updateExtents()

    def closeEvent(self, evt):
        """
        Clean up layers when the dialog is closed.
        """
        if self.square_layer is not None:
            QgsProject.instance().removeMapLayer(self.square_layer)
            self.square_layer = None
