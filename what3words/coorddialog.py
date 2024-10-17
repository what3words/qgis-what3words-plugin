from builtins import str
import os
from PyQt5.QtWidgets import (QLineEdit, QDockWidget, QHBoxLayout, QVBoxLayout,
                             QListWidget, QListWidgetItem, QWidget, QCheckBox, QApplication)
from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor, QPalette
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting
from what3words.shared_layer_point import W3WPointLayerManager
from what3words.w3w import what3words

class W3WCoordInputDialog(QDockWidget):
    def __init__(self, canvas, parent):
        self.canvas = canvas
        self.zoom_level = 19  # Default zoom level
        QDockWidget.__init__(self, parent)
        self.setAllowedAreas(Qt.TopDockWidgetArea)
        self.point_layer_manager = W3WPointLayerManager.getInstance()  # Use the shared point layer
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
                    item_text = f"///{suggestion['words']}, {suggestion['nearestPlace']}"
                    item = QListWidgetItem(item_text)
                    self.suggestionsList.addItem(item)

                self.suggestionsList.setVisible(True)  # Show suggestions
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
        self.coordBox.setText(selected_text.split(',')[0].replace("///", ""))  # Update the input box with the selected address
        self.suggestionsList.setVisible(False)  # Hide the suggestions list
        self.showW3WPoint()

    def showW3WPoint(self, selected_text=None):
        """
        Show the W3W point on the map when a suggestion is selected.
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

            # Make the API call to get the what3words point
            response_json = self.w3w.convertToCoordinates(w3wCoord)

            # Add the W3W point to the shared layer
            self.point_layer_manager.addPointFeature(response_json)

            # Zoom to the point location
            lat = float(response_json["coordinates"]["lat"])
            lon = float(response_json["coordinates"]["lng"])
            canvasCrs = self.canvas.mapSettings().destinationCrs()
            epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
            transform4326 = QgsCoordinateTransform(epsg4326, canvasCrs, QgsProject.instance())
            center = transform4326.transform(lon, lat)
            self.canvas.setCenter(center)
            self.canvas.zoomScale(591657550.5 / (2 ** self.zoom_level))  # Adjust the zoom level
            self.canvas.refresh()

        except Exception as e:
            iface.messageBar().pushMessage("what3words", f"The Error is: {str(e)}", level=Qgis.Warning, duration=5)
        finally:
            QApplication.restoreOverrideCursor()