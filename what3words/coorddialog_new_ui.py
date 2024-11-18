import os
import csv
import webbrowser

from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QSizePolicy, QApplication, QDockWidget, QListWidget, QListWidgetItem, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from qgis.core import Qgis, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsFeature, QgsGeometry
from qgis.gui import QgsVertexMarker
from qgis.utils import iface

from qgiscommons2.settings import pluginSetting
from qgiscommons2.gui.settings import ConfigDialog

from what3words.maptool import W3WMapTool
from what3words.grid import W3WGridManager
from what3words.shared_layer_point import W3WPointLayerManager
from what3words.w3w import what3words, GeoCodeException
from what3words.ui.coorddialog_ui import Ui_discoverToWhat3words  # Import the generated UI class
ICON_PATH = os.path.join(os.path.dirname(__file__), "icons")

class W3WCoordInputDialog(QDockWidget, Ui_discoverToWhat3words):
    def __init__(self, canvas, parent):
        super(W3WCoordInputDialog, self).__init__(parent)
        self.canvas = canvas
        self.zoom_level = 19  # Default zoom level
        self.setupUi(self)  # Set up the UI from coorddialog_ui.py
        self.setAllowedAreas(Qt.TopDockWidgetArea)
        self.point_layer_manager = W3WPointLayerManager.getInstance()
        self.mapTool = W3WMapTool(self.canvas, self)
        self.mapToolForMapsite = W3WMapTool(self.canvas, self)
        self.mapToolForMapsite.w3wAddressCapturedForMapsite.connect(self.openMapsiteInBrowser)
        self.gridManager = None 
        self.allowClosing = True
        apiKey = pluginSetting("apiKey", namespace="what3words")
        addressLanguage = pluginSetting("addressLanguage", namespace="what3words")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)
        
        self.initGui()

    def initGui(self):
        self.w3wCaptureButton.setIcon(QIcon(os.path.join(ICON_PATH, "w3w_marker.svg")))
        self.viewGridButton.setIcon(QIcon(os.path.join(ICON_PATH, "grid_red.svg")))
        self.saveToFileButton.setIcon(QIcon(':/images/themes/default/mActionFileSave.svg'))
        self.openMapsiteButton.setIcon(QIcon(os.path.join(ICON_PATH, "w3w_search.svg")))
        self.settingsButton.setIcon(QIcon(':/images/themes/default/mActionOptions.svg'))
        self.createLayerButton.setIcon(QIcon(":images/themes/default/mActionAddOgrLayer.svg"))
        self.clearMarkersButton.setIcon(QIcon(':/images/themes/default/mIconClearText.svg'))
        self.deleteSelectedButton.setIcon(QIcon(':/images/themes/default/mActionDeleteSelected.svg'))
        self.clearAll.setIcon(QIcon(":images/themes/default/mActionDeselectAll.svg"))

        # Connect signals from UI elements to the respective functions
        self.w3wCaptureButton.clicked.connect(self.toggleCaptureTool)
        self.w3wCaptureButton.setCheckable(True)

        self.viewGridButton.clicked.connect(self.toggleGrid)
        self.viewGridButton.setCheckable(True)

        self.saveToFileButton.clicked.connect(self.saveToFile)
        # self.saveToFileButton.setCheckable(False)

        self.openMapsiteButton.clicked.connect(self.toggleMapToolForMapsite)
        self.openMapsiteButton.setCheckable(True)

        self.settingsButton.clicked.connect(self.showSettingsDialog)
        self.settingsButton.setCheckable(True)

        self.tableWidget.itemSelectionChanged.connect(self.onTableItemSelected)
        self.tableWidget.setEditTriggers(QHeaderView.NoEditTriggers)

        self.showAllMarkersCheckBox.setChecked(True)
        self.showAllMarkersCheckBox.stateChanged.connect(self.toggleMarkerDisplay)

        self.clearMarkersButton.clicked.connect(self.clearMarkers)
        self.createLayerButton.clicked.connect(self.handleSaveToLayer)

        self.deleteSelectedButton.clicked.connect(self.deleteSelectedRow)
        self.clearAll.clicked.connect(self.clearAllRows)

        # Connect text change in the input field to suggestions
        self.addLineEdit.textChanged.connect(self.suggestW3W)
        self.listWidget = QListWidget(self.dockWidgetContents)
        self.listWidget.setVisible(False) 
        self.listWidget.itemClicked.connect(self.onSuggestionSelected)
        self.inputField.setContentsMargins(0, 0, 0, 0)
        self.inputField.setSpacing(0)

        # Add the listWidget just below the inputField
        self.inputField.addWidget(self.listWidget, 1, 0, 1, 2)

        # Set up the table widget
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(["what3words", "Latitude", "Longitude", "Nearest Place", "Country", "Language"])
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Handle dark mode styling
        self.handleDarkMode()
    
    ## Table handling
    def addRowToTable(self, w3w_address, lat, lon, nearest_place, country, language):
        """
        Adds a new row to the table with what3words data.
        """
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)
        # List of columns with values and editability
        columns = [
            (w3w_address, False),  # Read-only
            (str(lat), False),     # Read-only
            (str(lon), False),     # Read-only
            (nearest_place, False),# Read-only
            (country, False),      # Read-only
            (language, False)     # Read-only
        ]

        # Add items to the table with the appropriate editability
        for col_index, (value, editable) in enumerate(columns):
            item = QTableWidgetItem(value)
            if not editable:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make item read-only
            self.tableWidget.setItem(row_position, col_index, item)

        # Temporarily block the selection signal to prevent triggering onTableItemSelected
        self.tableWidget.blockSignals(True)
        self.tableWidget.selectRow(row_position)  # Select the new row
        self.tableWidget.scrollToItem(self.tableWidget.item(row_position, 0))  # Scroll to the new row
        self.tableWidget.blockSignals(False)  # Re-enable the selection signal

        QApplication.clipboard().setText(w3w_address)
        iface.messageBar().pushMessage(
            "what3words", 
            f"Added '{w3w_address}' to the table and copied to clipboard.", 
            level=Qgis.Success, duration=3
        )
    
    def onTableItemSelected(self):
        """Handles the table row selection, updating markers without zooming."""
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            return

        # Retrieve latitude and longitude from the selected row
        row = selected_items[0].row()
        lat = float(self.tableWidget.item(row, 1).text())
        lon = float(self.tableWidget.item(row, 2).text())

        # Convert coordinates to map CRS
        point_map_crs = self.get_map_coordinate_from_lat_lon(lat, lon)

        # Clear existing markers if Show All Markers is not checked
        if not self.showAllMarkersCheckBox.isChecked():
            for marker in self.storedMarkers:
                self.canvas.scene().removeItem(marker)
            self.storedMarkers = [marker for marker in self.storedMarkers if marker.center() != point_map_crs]

        # Add marker for the selected row
        self.addMarker(point_map_crs)
        self.flashMarker(point_map_crs)
        self.canvas.refresh()

    def get_map_coordinate_from_lat_lon(self, lat, lon):
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(epsg4326, canvasCrs, QgsProject.instance())

        # Transform point from WGS84 to map CRS
        point_wgs84 = QgsPointXY(lon, lat)
        point_map_crs = transform.transform(point_wgs84)
        return point_map_crs

    def flashMarker(self, point):
        """Adds a temporary marker that flashes briefly on the map."""
        if not hasattr(self, 'flashMarkerInstance'):
            self.flashMarkerInstance = QgsVertexMarker(self.canvas)
            self.flashMarkerInstance.setIconType(QgsVertexMarker.ICON_CROSS)
            self.flashMarkerInstance.setColor(Qt.yellow)
            self.flashMarkerInstance.setIconSize(30)
            self.flashMarkerInstance.setPenWidth(6)

        self.flashMarkerInstance.setCenter(point)
        self.flashMarkerInstance.show()

        # Hide the marker after a short delay
        QTimer.singleShot(1000, self.flashMarkerInstance.hide)
        self.canvas.refresh()

    def deleteSelectedRow(self):
        """Remove selected entries from the coordinate table and corresponding markers from the map."""
        indices = [x.row() for x in self.tableWidget.selectionModel().selectedRows()]
        if not indices:
            return

        # Confirmation dialog for deletion
        reply = QMessageBox.question(
            self, 'Message',
            'Are you sure you want to delete the selected locations?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Block signals to prevent unwanted actions during deletion
            self.tableWidget.blockSignals(True)
            tolerance = 1e-6  # Tolerance level for precise coordinate matching

            for row in sorted(indices, reverse=True):
                # Retrieve latitude and longitude from the selected row
                lat = float(self.tableWidget.item(row, 1).text())
                lon = float(self.tableWidget.item(row, 2).text())

                # Convert the coordinates from WGS84 to the map CRS to match marker positions accurately
                point_map_crs = self.get_map_coordinate_from_lat_lon(lat, lon)

                # Find and remove matching markers
                markers_to_remove = [
                    marker for marker in self.storedMarkers
                    if abs(marker.center().x() - point_map_crs.x()) < tolerance and
                    abs(marker.center().y() - point_map_crs.y()) < tolerance
                ]

                for marker in markers_to_remove:
                    self.canvas.scene().removeItem(marker)
                    self.storedMarkers.remove(marker)

                # Remove the row from the table
                self.tableWidget.removeRow(row)

            # Unblock signals and clear selection
            self.tableWidget.blockSignals(False)
            self.tableWidget.clearSelection()

    def clearAllRows(self):
        """
        Deletes all rows from the table.
        """
        reply = QMessageBox.question(
            self, 'Message', 'Are your sure you want to delete all locations?',
            QMessageBox.Yes, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.tableWidget.blockSignals(True)
            self.removeMarkers()
            self.tableWidget.setRowCount(0)
            self.tableWidget.blockSignals(False)
    
    ## Capture tool handling
    def toggleCaptureTool(self):
        """
        Activates or deactivates the what3words map tool for capturing map clicks to convert them into 3-word addresses.
        """
        apiKey = pluginSetting("apiKey", namespace="what3words")
        if not apiKey:
            iface.messageBar().pushMessage("what3words", "API key missing. Please set the API key in plugin settings.", level=Qgis.Warning, duration=2)
            self.w3wCaptureButton.setChecked(False)
            return

        # Toggle the map tool on or off based on its current state
        if self.canvas.mapTool() == self.mapTool:
            self.canvas.unsetMapTool(self.mapTool)
            self.w3wCaptureButton.setChecked(False)
            iface.messageBar().pushMessage("what3words", "View what3words Tool deactivated.", level=Qgis.Info, duration=2)
        else:
            # Ensure only mapTool is activated without affecting mapToolForMapsite
            self.canvas.unsetMapTool(self.mapToolForMapsite)  # Ensure mapsite tool is inactive
            self.canvas.setMapTool(self.mapTool)
            self.w3wCaptureButton.setChecked(True)
            iface.messageBar().pushMessage("what3words", "View what3words Tool activated. Click on the map to get what3words address.", level=Qgis.Info, duration=2)

    ## Grid handling
    def toggleGrid(self):
        """
        Toggles the What3words grid on and off and updates the button's checked state.
        """
        apiKey = pluginSetting("apiKey", namespace="what3words")
        if not apiKey:
            iface.messageBar().pushMessage("what3words", "API key missing. Please set the API key in plugin settings.", level=Qgis.Warning, duration=2)
            self.viewGridButton.setChecked(False)
            return

        # Initialize gridManager if it doesn't exist
        if self.gridManager is None:
            self.gridManager = W3WGridManager(self.canvas)

        # Toggle the grid based on current state
        if self.viewGridButton.isChecked():
            self.gridManager.enableGrid(True)
            iface.messageBar().pushMessage("what3words", "Grid enabled.", level=Qgis.Info, duration=2)
        else:
            self.gridManager.enableGrid(False)
            iface.messageBar().pushMessage("what3words", "Grid disabled.", level=Qgis.Info, duration=2)

    ## Settings handling
    def showSettingsDialog(self):
        """
        Opens the settings dialog if it's not already open. Disables the settings button
        while the dialog is open and re-enables it when the dialog is closed.
        """
        # Check if the dialog is already open
        if hasattr(self, 'settingsDialog') and self.settingsDialog is not None:
            # Bring the dialog to the front if it's already open
            self.settingsDialog.raise_()
            return

        # Check if the dialog is already open
        if not hasattr(self, 'settingsDialog') or self.settingsDialog is None:
            # Attempt to open the settings dialog
            self.settingsDialog = ConfigDialog("what3words")

            # Ensure the settings button is re-enabled when the dialog is closed
            self.settingsDialog.finished.connect(self.onSettingsDialogClosed)

        # Disable the settings button while dialog is open
        self.settingsButton.setEnabled(False)

        # Show the dialog
        self.settingsDialog.show()

    def onSettingsDialogClosed(self):
        """
        Callback when the settings dialog is closed. Re-enables the settings button.
        """
        self.settingsButton.setEnabled(True)
        self.settingsDialog = None  # Reset dialog reference

    ## Dark mode handling   
    def handleDarkMode(self):
        """Adjusts the input box style for dark mode."""
        palette = self.addLineEdit.palette()
        palette.setColor(self.addLineEdit.foregroundRole(), Qt.black)
        palette.setColor(self.addLineEdit.backgroundRole(), Qt.white)
        self.addLineEdit.setPalette(palette)

    ## Layer handling
    def handleSaveToLayer(self):
        """
        Saves all records from the table to a new layer. If there are no records, shows an error message.
        """
        if self.tableWidget.rowCount() == 0:
            iface.messageBar().pushMessage(
                "what3words", "No records in the table to save.", level=Qgis.Warning, duration=2
            )
            return

        # Create a new temporary point layer
        new_layer = self.point_layer_manager.createPointLayer()

        # Check if the new layer was created successfully
        if not new_layer:
            iface.messageBar().pushMessage(
                "what3words", "Failed to create a new layer. Please try again.", level=Qgis.Critical, duration=3
            )
            return

        # Loop through each row in the table and save to the layer
        features = []
        for row in range(self.tableWidget.rowCount()):
            w3w_address = self.tableWidget.item(row, 0).text()
            latitude = float(self.tableWidget.item(row, 1).text())
            longitude = float(self.tableWidget.item(row, 2).text())
            nearest_place = self.tableWidget.item(row, 3).text()
            country = self.tableWidget.item(row, 4).text()
            language = self.tableWidget.item(row, 5).text()

            # Create the data structure for the point feature
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(longitude, latitude)))
            feature.setAttributes([
                w3w_address,
                latitude,
                longitude,
                nearest_place,
                country,
                language
            ])
            features.append(feature)

        # Add all features to the new layer
        if features:
            new_layer.dataProvider().addFeatures(features)
            new_layer.updateExtents()
            new_layer.triggerRepaint()

        iface.messageBar().pushMessage(
            "what3words", f"All records saved to the new layer '{new_layer.name()}'.", level=Qgis.Success, duration=3
        )

    def saveToLayer(self, point_data):
        """
        Adds a point feature to the layer using provided data.
        """
        try:
            # Recheck and recreate the point layer if it has been deleted
            if not self.point_layer_manager.layerExists():
                self.point_layer_manager.createPointLayer()

            # Add point feature to the layer using point_data structure
            self.point_layer_manager.addPointFeature(point_data)

        except Exception as e:
            iface.messageBar().pushMessage("what3words", f"Error saving to layer: {str(e)}", level=Qgis.Warning, duration=2)

    ## Suggestions handling
    def suggestW3W(self, text):
        """Fetches autosuggest suggestions for a partial what3words address."""
        self.listWidget.clear()
        self.listWidget.setVisible(False)

        apiKey = pluginSetting("apiKey", namespace="what3words")
        addressLanguage = pluginSetting("addressLanguage", namespace="what3words")

        if not apiKey:
            iface.messageBar().pushMessage("what3words", "API key missing. Please set the API key in plugin settings.", level=Qgis.Warning, duration=2)
            return

        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)

        # Validate what3words address format
        if not self.w3w.is_possible_3wa(text):
            return

        try:
            suggestions = self.w3w.autosuggest(text)

            if not suggestions.get('suggestions'):
                error_message = suggestions.get('error', {}).get('message', 'No suggestions found.')
                iface.messageBar().pushMessage("what3words", error_message, level=Qgis.Warning, duration=2)
                return

            self.populateSuggestionsList(suggestions['suggestions'])

        except Exception as e:
            iface.messageBar().pushMessage("what3words", f"Network error: {str(e)}", level=Qgis.Warning, duration=2)

    def populateSuggestionsList(self, suggestions):
        """Populates the suggestions list widget with items from the suggestions data."""
        self.listWidget.clear()  # Clear any previous suggestions

        if not suggestions:
            self.listWidget.setVisible(False)  # Hide listWidget if no suggestions
            return
        
        for suggestion in suggestions:
            item_text = f"///{suggestion['words']}, {suggestion['nearestPlace']}"
            self.listWidget.addItem(QListWidgetItem(item_text))

        self.listWidget.setVisible(True)
        self.adjustSuggestionsListSize(len(suggestions))

    def adjustSuggestionsListSize(self, num_items):
        """Adjusts the size and styling of the suggestions list."""
        total_height = 60  # Fixed height of 100px
        self.listWidget.setFixedHeight(total_height)
        self.listWidget.setFixedWidth(self.addLineEdit.width())
        self.listWidget.setStyleSheet("""
            QListWidget { background-color: #FFFFFF; color: #000000; padding: 0px; border: 1px solid #E0E0E0; }
            QListWidget::item { padding: 2px 6px; color: #000000; }
            QListWidget::item:selected { background-color: #E0E0E0; color: #000000; }
        """)
        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Show vertical scrollbar if necessary
        self.listWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        

    def onSuggestionSelected(self, item):
        """Handles the event when a suggestion is selected from the list."""
        w3w_address = item.text().split(',')[0].replace("///", "")
        self.addLineEdit.setText(w3w_address)
        self.listWidget.setVisible(False)  # Hide the suggestions list
        self.fetchAndDisplayDetails(w3w_address)
        self.showW3WPoint()

    def showW3WPoint(self, selected_text=None):
        """Show the W3W point on the map when a suggestion is selected."""
        apiKey = pluginSetting("apiKey", namespace="what3words")
        addressLanguage = pluginSetting("addressLanguage", namespace="what3words")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)

        try:
            if selected_text is None:
                w3wCoord = str(self.addLineEdit.text()).replace(" ", "")
            else:
                w3wCoord = str(selected_text).replace(" ", "")
            
            response_json = self.w3w.convertToCoordinates(w3wCoord)
            lat = float(response_json["coordinates"]["lat"])
            lng = float(response_json["coordinates"]["lng"])

            # Convert coordinates to map CRS
            center = self.get_map_coordinate_from_lat_lon(lat, lng)
            
            self.addMarker(center)

            self.canvas.setCenter(center)
            self.canvas.zoomScale(591657550.5 / (2 ** self.zoom_level))
            self.canvas.refresh()

        except GeoCodeException as e:
            iface.messageBar().pushMessage("what3words", str(e), level=Qgis.Critical, duration=2)
        finally:
            QApplication.restoreOverrideCursor()        
    
    def fetchAndDisplayDetails(self, w3w_address):
        """Fetches W3W details for the selected address and displays them in the table."""
        try:
            response_json = self.w3w.convertToCoordinates(w3w_address)
            lat = response_json["coordinates"]["lat"]
            lng = response_json["coordinates"]["lng"]
            nearest_place = response_json.get("nearestPlace", "")
            country = response_json.get("country", "")
            language = response_json.get("language", "")

            # Add details to the table
            self.addRowToTable(w3w_address, lat, lng, nearest_place, country, language)

        except GeoCodeException as e:
            iface.messageBar().pushMessage("what3words", str(e), level=Qgis.Critical, duration=2)
    
    # Bounding box handling
    def getBoundingBox(self):
        """Returns a bounding box string in EPSG:4326 coordinates for the current map extent."""
        extent = self.canvas.extent()
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        transform4326 = QgsCoordinateTransform(canvasCrs, epsg4326, QgsProject.instance())
        bottom_left = transform4326.transform(extent.xMinimum(), extent.yMinimum())
        top_right = transform4326.transform(extent.xMaximum(), extent.yMaximum())
        return f"{bottom_left.y()},{bottom_left.x()},{top_right.y()},{top_right.x()}"

    ## File handling
    def saveToFile(self):
        """
        Saves the table data to a CSV file if there are records in the table.
        """
        # Check if the table has any records
        if self.tableWidget.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No records available to save.")
            return

        # Open file dialog for saving
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        file_dialog.setDefaultSuffix("csv")

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]

            try:
                # Open the CSV file for writing
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    
                    # Write the header
                    headers = ["what3words", "Latitude", "Longitude", "Nearest Place", "Country", "Language"]
                    writer.writerow(headers)
                    
                    # Write each row of data from the table
                    for row in range(self.tableWidget.rowCount()):
                        row_data = [self.tableWidget.item(row, col).text() for col in range(self.tableWidget.columnCount())]
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Success", f"Data saved successfully to {file_path}.")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file. Error: {str(e)}")

    ## Mapsite handling   
    def toggleMapToolForMapsite(self):
        apiKey = pluginSetting("apiKey", namespace="what3words")
        if not apiKey:
            iface.messageBar().pushMessage("what3words", "API key missing. Please set the API key in plugin settings.", level=Qgis.Warning, duration=2)
            self.openMapsiteButton.setChecked(False)
            return

        # Toggle the map tool exclusively for mapsite functionality
        if self.canvas.mapTool() == self.mapToolForMapsite:
            self.canvas.unsetMapTool(self.mapToolForMapsite)
            self.openMapsiteButton.setChecked(False)
            iface.messageBar().pushMessage("what3words", "Open mapsite tool deactivated.", level=Qgis.Info, duration=2)
        else:
            # Ensure only mapToolForMapsite is activated without affecting mapTool
            self.canvas.unsetMapTool(self.mapTool)  # Ensure capture tool is inactive
            self.canvas.setMapTool(self.mapToolForMapsite)
            self.openMapsiteButton.setChecked(True)
            iface.messageBar().pushMessage("what3words", "Open mapsite tool activated. Click on the map to get the what3words address.", level=Qgis.Info, duration=2)
    
    def openMapsiteInBrowser(self, w3w_address):
        """Opens the specified what3words address in the browser."""
        w3w_url = f"https://what3words.com/{w3w_address}?application=qgis"
        webbrowser.open(w3w_url)
        iface.messageBar().pushMessage("what3words", f"Opening URL: {w3w_url}", level=Qgis.Info, duration=2)

    ## Marker handling
    def addMarker(self, point):
        """
        Adds a marker to the map and stores it in `storedMarkers`.
        """
        if not self.showAllMarkersCheckBox.isChecked():
            for marker in self.storedMarkers:
                self.canvas.scene().removeItem(marker)

        marker = QgsVertexMarker(self.canvas)
        marker.setIconType(QgsVertexMarker.ICON_CROSS)
        marker.setColor(Qt.red)
        marker.setIconSize(18)
        marker.setPenWidth(2)
        marker.setCenter(point)
        self.canvas.scene().addItem(marker) 
        self.storedMarkers.append(marker)

    def clearMarkers(self):
        """
        Hides all markers from the map view without removing them from storedMarkers,
        allowing them to be restored if Show All Markers is rechecked.
        """
        self.showAllMarkersCheckBox.setChecked(False)
        # Hide all markers from the map
        for marker in self.storedMarkers:
            if marker is not None:
                self.canvas.scene().removeItem(marker)
            
        # Clear any selections in the table widget to avoid triggering item selection events
        self.tableWidget.blockSignals(True)
        self.tableWidget.clearSelection()
        self.tableWidget.blockSignals(False)

        iface.messageBar().pushMessage("what3words", "Markers hidden from the map. Use 'Show All Markers' to display them again.", level=Qgis.Info, duration=2)
    
    def removeMarkers(self):
        """
        Removes all markers from the map view and clears the storedMarkers list.
        """
        for marker in self.storedMarkers:
            if marker is not None:
                self.canvas.scene().removeItem(marker)
        self.storedMarkers.clear()

    def toggleMarkerDisplay(self):
        """
        Toggle showing all markers on the map based on the Show All Markers checkbox state.
        - If checked, add markers for all records in the table to the map.
        - If unchecked, remove all markers from the map except the marker from the selected row.
        """
        if self.showAllMarkersCheckBox.isChecked():
            # Show all markers
            for marker in self.storedMarkers:
                if marker is not None:
                    self.canvas.scene().addItem(marker)
        else:
            # Hide all markers first
            for marker in self.storedMarkers:
                if marker is not None:
                    self.canvas.scene().removeItem(marker)

            # Show only the last marker
            if self.storedMarkers:
                last_marker = self.storedMarkers[-1]  # Get the last marker in the list
                if last_marker is not None:
                    self.canvas.scene().addItem(last_marker)

    def closeEvent(self, event):
            """
            Prevents closing the dock widget if not explicitly allowed.
            Updates the button state when closed.
            """
            if self.allowClosing:
                # Reset the button state to unchecked when closed
                if hasattr(self, 'coordDialogAction') and self.coordDialogAction:
                    self.coordDialogAction.setChecked(False)
                super(W3WCoordInputDialog, self).closeEvent(event)
            else:
                event.ignore()  # Block the closing action
                
        