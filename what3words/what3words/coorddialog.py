from builtins import str
import os
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QLineEdit, QDockWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QWidget, QCheckBox, QApplication, QSizePolicy)
from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsPointXY, QgsVectorLayer, QgsFeature,
                       QgsGeometry, QgsField, QgsFillSymbol, QgsSimpleFillSymbolLayer, QgsSvgMarkerSymbolLayer)
from qgis.PyQt.QtCore import Qt, QStringListModel, QVariant
from qgis.PyQt.QtGui import QCursor, QPalette
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting

from what3words.w3w import what3words

class W3WCoordInputDialog(QDockWidget):
    def __init__(self, canvas, parent):
        self.canvas = canvas
        self.marker_layer = None
        self.square_layer = None
        self.zoom_level = 19  # Default zoom level
        QDockWidget.__init__(self, parent)
        self.setAllowedAreas(Qt.TopDockWidgetArea)
        self.initGui()

    def setApiKey(self, apikey):
        self.w3w = what3words(apikey=apikey)

    def setAddressLanguage(self, addressLanguage):
        self.w3w = what3words(addressLanguage=addressLanguage)

    def initGui(self):
        self.setWindowTitle("Zoom to what3words address")

        # Input field for the what3words address
        self.coordBox = QLineEdit()
        self.coordBox.setPlaceholderText("e.g. ///filled.count.soap")

        # Suggestions list widget
        self.suggestionsList = QListWidget()
        self.suggestionsList.setVisible(False)  # Hide the list until we have suggestions
        self.suggestionsList.itemClicked.connect(self.onSuggestionSelected)  # Handle suggestion click

        # Button to display W3W square
        self.showSquareButton = QPushButton("Zoom To")
        self.showSquareButton.setEnabled(False)  # Initially disabled
        self.showSquareButton.clicked.connect(self.showW3WSquare)

        # Checkbox for enabling bounding box
        self.boundingBoxCheckbox = QCheckBox("Use Bounding Box")

        # Layout setup
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.coordBox)
        hlayout.addWidget(self.boundingBoxCheckbox)  # Align checkbox next to input field

        # Vertical layout to place suggestions below input field
        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.suggestionsList)

        # Set the widget layout
        dockWidgetContents = QWidget()
        dockWidgetContents.setLayout(vlayout)
        self.setWidget(dockWidgetContents)

        # Connect the text change event to fetch suggestions
        self.coordBox.textChanged.connect(self.suggestW3W)

        # Handle dark mode
        self.handleDarkMode()

    def handleDarkMode(self):
        """
        Adjusts the input box style for dark mode, forcing text color to be visible.
        """
        palette = self.coordBox.palette()
        palette.setColor(QPalette.Text, Qt.black)  # Force text to be black
        palette.setColor(QPalette.Base, Qt.white)  # Set background to white
        self.coordBox.setPalette(palette)

    def suggestW3W(self, text):
        """
        Fetches suggestions based on the input text for autosuggest functionality.
        Trigger suggestions after at least the first letter of the 3rd word is entered.
        If the bounding box checkbox is checked, clip the suggestions to the map view.
        """

        self.suggestionsList.clear()  # Clear previous suggestions
        self.suggestionsList.setVisible(False)  # Hide the list initially

        apiKey = pluginSetting("apiKey")
        addressLanguage = pluginSetting("addressLanguage")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)

        # Ensure this is a possible what3words address format
        if not self.w3w.is_possible_3wa(text):
            return

        try:
            # Check if the bounding box checkbox is checked
            if self.boundingBoxCheckbox.isChecked():
                # Apply bounding box if checkbox is checked
                extent = self.canvas.extent()
                canvasCrs = self.canvas.mapSettings().destinationCrs()
                epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
                transform4326 = QgsCoordinateTransform(canvasCrs, epsg4326, QgsProject.instance())
                bottom_left = transform4326.transform(extent.xMinimum(), extent.yMinimum())
                top_right = transform4326.transform(extent.xMaximum(), extent.yMaximum())
                bbox = f"{bottom_left.y()},{bottom_left.x()},{top_right.y()},{top_right.x()}"
                suggestions = self.w3w.autosuggest(text, clip_to_bounding_box=bbox)
            else:
                # Fetch suggestions without bounding box
                suggestions = self.w3w.autosuggest(text)

            # Ensure we have suggestions in the response
            if 'suggestions' in suggestions and len(suggestions['suggestions']) > 0:
                for suggestion in suggestions['suggestions']:
                    # Customize display format: "///filled.count.soap, NearestPlace, Country"
                    item_text = f"///{suggestion['words']}, {suggestion['nearestPlace']}, {suggestion['country']}"
                    item = QListWidgetItem()
                    item.setText(item_text)
                    item.setTextAlignment(Qt.AlignLeft)
                    self.suggestionsList.addItem(item)

                # Adjust the height to fit the number of lines without scrollbar
                self.suggestionsList.setVisible(True)

                # Fix height to show 3 items (adjust row size accordingly)
                num_items = min(len(suggestions['suggestions']), 3)
                total_height = self.suggestionsList.sizeHintForRow(0) * num_items
                self.suggestionsList.setFixedHeight(total_height)

                # Set a fixed width for the suggestion list to prevent horizontal scrolling
                self.suggestionsList.setFixedWidth(self.coordBox.width())

                # Set the style for the suggestions dropdown
                self.suggestionsList.setStyleSheet("""
                    QListWidget {
                        background-color: white; 
                        color: #000000; 
                        padding: 0px; 
                        border: 1px solid #E0E0E0;
                    }
                    QListWidget::item {
                        padding: 2px 6px;
                        color: #000000;
                    }
                    QListWidget::item:selected {
                        background-color: #E0E0E0; 
                        color: #696969; 
                    }
                """)

                # Ensure scrollbars are disabled
                self.suggestionsList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.suggestionsList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

                # Adjust the height to fit the contents
                num_items = self.suggestionsList.count()
                item_height = self.suggestionsList.sizeHintForRow(0)
                total_height = item_height * num_items
                self.suggestionsList.setFixedHeight(total_height)

                # Position the dropdown directly below the input field
                self.suggestionsList.move(self.coordBox.x(), self.coordBox.y() + self.coordBox.height())

                # Set size policy to ensure no extra space is allocated
                self.suggestionsList.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        except Exception as e:
            pass  # Silently fail for suggestions fetching

    def onSuggestionSelected(self, item):
        """
        Handles the event when a suggestion is selected from the list.
        """
        selected_text = item.text()  # Get the selected what3words address
        self.coordBox.setText(selected_text.split(',')[0].replace("<span style='color:red'>///", "").replace("</span>", ""))  # Update the input box with the selected address        self.suggestionsList.setVisible(False)  # Hide the suggestions list
        self.suggestionsList.setVisible(False)  # Hide the suggestions list
        self.showW3WSquare()

    def showW3WSquare(self, selected_text=None):
        """
        Show the W3W square on the map when a suggestion is selected.
        """
        apiKey = pluginSetting("apiKey")
        addressLanguage = pluginSetting("addressLanguage")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)

        try:
            # Get the selected what3words address
            if selected_text is None:
                w3wCoord = str(self.coordBox.text()).replace(" ", "")
            else:
                w3wCoord = str(selected_text).replace(" ", "")

            # Make the API call to get the what3words square
            response_json = self.w3w.convertToCoordinates(w3wCoord)

            # Check if required keys are present in the API response
            if 'coordinates' not in response_json or 'square' not in response_json or 'words' not in response_json:
                raise ValueError("Invalid API response: Missing required data.")

            # Get the canvas CRS (coordinate reference system)
            canvasCrs = self.canvas.mapSettings().destinationCrs()

            # Draw the what3words square on the map using the response data and canvas CRS
            self.drawW3WSquare(response_json, canvasCrs)

            # Zoom to the center point of the square
            lat = float(response_json["coordinates"]["lat"])
            lon = float(response_json["coordinates"]["lng"])
            epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
            transform4326 = QgsCoordinateTransform(epsg4326, canvasCrs, QgsProject.instance())
            center = transform4326.transform(lon, lat)
            self.canvas.setCenter(center)
            self.canvas.zoomScale(591657550.5 / (2 ** self.zoom_level))  # Adjust the zoom level
            self.canvas.refresh()

        except ValueError as ve:
            iface.messageBar().pushMessage("what3words", f"Value Error: {str(ve)}", level=Qgis.Warning, duration=5)
        except Exception as e:
            iface.messageBar().pushMessage("what3words", f"The Error is: {str(e)}", level=Qgis.Warning, duration=5)
        finally:
            QApplication.restoreOverrideCursor()

    def drawW3WSquare(self, json, canvasCrs):
        """
        Draw the what3words square as a polygon on the map and use an SVG marker as fill.
        """
        square = json["square"]

        # Check if 'square', 'coordinates', and 'words' exist in the API response
        if 'southwest' not in square or 'northeast' not in square:
            iface.messageBar().pushMessage("what3words", "Invalid API response: Missing square data.", level=Qgis.Critical, duration=5)
            return

        # Coordinates of the square
        southwest = square["southwest"]
        northeast = square["northeast"]

        # Create the polygon for the square in EPSG:4326 (WGS84)
        bottom_left = QgsPointXY(southwest["lng"], southwest["lat"])
        top_right = QgsPointXY(northeast["lng"], northeast["lat"])
        top_left = QgsPointXY(southwest["lng"], northeast["lat"])
        bottom_right = QgsPointXY(northeast["lng"], southwest["lat"])

        points = [bottom_left, top_left, top_right, bottom_right, bottom_left]
        polygon = QgsGeometry.fromPolygonXY([points])

        # Check if the square_layer still exists and is valid
        if not self.square_layer or not QgsProject.instance().mapLayersByName(self.square_layer.name()):
            # The layer doesn't exist anymore or is invalid, recreate it
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

        # Ensure the square layer is valid before adding features
        if self.square_layer:
            self.square_layer.dataProvider().addFeatures([feature])
            self.square_layer.updateExtents()

            # Apply SVG marker for the square
            svg_path = os.path.join(os.path.dirname(__file__), 'icons', 'w3w.svg')
            if os.path.exists(svg_path):
                symbol = QgsFillSymbol()

                # Add a simple fill layer for the polygon
                simple_fill_layer = QgsSimpleFillSymbolLayer()
                symbol.changeSymbolLayer(0, simple_fill_layer)

                # Add the SVG marker at the centroid of the square
                svg_marker_layer = QgsSvgMarkerSymbolLayer(svg_path)
                symbol.appendSymbolLayer(svg_marker_layer)

                # Set the renderer for the layer
                self.square_layer.renderer().setSymbol(symbol)
                self.square_layer.triggerRepaint()


    def closeEvent(self, evt):
        """
        Clean up layers when the dialog is closed.
        """
        if self.square_layer is not None:
            QgsProject.instance().removeMapLayer(self.square_layer)
            self.square_layer = None
