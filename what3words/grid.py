import os
import json

from qgis.core import (Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint,
                       QgsLineSymbol, QgsSingleSymbolRenderer, QgsMapLayer,
                       QgsField, QgsVectorFileWriter)
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication, QFileDialog, QMessageBox
from qgis.utils import iface
from qgiscommons2.settings import pluginSetting
from what3words.w3w import what3words, GeoCodeException



class W3WGridManager:
    
    epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

    def __init__(self, canvas):
        self.canvas = canvas
        apiKey = pluginSetting("apiKey", namespace="what3words")
        addressLanguage = pluginSetting("addressLanguage", namespace="what3words")
        self.w3w = what3words(apikey=apiKey, addressLanguage=addressLanguage)
        self.grid_layer = None 
        self.grid_enabled = False  
        self.geojson_path = os.path.join(os.path.dirname(__file__), "w3w_grid.geojson")
        self.last_grid_extent = None  # Track last fetched grid extent

    def enableGrid(self, enable=True):
        """
        Enables or disables the automatic fetching of the W3W grid based on map movement.
        """
        self.grid_enabled = enable

        if enable:
            try:
                # Ensure the grid layer exists
                if not self.grid_layer or not QgsProject.instance().mapLayersByName(self.grid_layer.name()):
                    self.ensureGridLayer()

                # Connect the signal to fetch and draw the grid
                iface.mapCanvas().extentsChanged.connect(self.fetchAndDrawW3WGrid)
                self.fetchAndDrawW3WGrid()
            except RuntimeError as e:
                iface.messageBar().pushMessage(
                    "what3words", 
                    "The grid layer has been manually deleted and cannot be recreated. Please reload the plugin.",
                    level=Qgis.Critical, duration=5
                )
        else:
            try:
                # Disconnect the signal if connected
                iface.mapCanvas().extentsChanged.disconnect(self.fetchAndDrawW3WGrid)
            except TypeError:
                # Handle the case where the signal is not connected
                iface.messageBar().pushMessage(
                    "what3words", 
                    "Grid is already disabled or not connected.",
                    level=Qgis.Warning, duration=2
                )

            # Optionally remove the grid layer if desired
            if self.grid_layer and QgsProject.instance().mapLayersByName(self.grid_layer.name()):
                self.removeGridLayer()

    def saveGridToFile(self):
        """
        Exports the grid layer to a GeoJSON file if the user chooses to save the grid.
        """
        if not self.grid_layer:
            iface.messageBar().pushMessage("Grid", "No grid layer to save.", level=Qgis.Warning)
            return

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            iface.mainWindow(),
            "Save Grid Layer As", "", "GeoJSON Files (*.geojson);;All Files (*)"
        )

        if file_path:
            QgsVectorFileWriter.writeAsVectorFormat(self.grid_layer, file_path, "utf-8", self.grid_layer.crs(), "GeoJSON")
            iface.messageBar().pushMessage("Grid", "Grid layer saved successfully.", level=Qgis.Info)
        else:
            iface.messageBar().pushMessage("Grid", "Save operation canceled.", level=Qgis.Warning)

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
        
        # Create an extent object to compare with the previous fetched extent
        current_extent = (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())
        
        # Skip API call if the current extent matches the last grid extent
        if self.last_grid_extent == current_extent:
            return
            
        # Get the map canvas CRS (which might not be WGS84)
        canvasCrs = self.canvas.mapSettings().destinationCrs()

        # Create a transform object to convert the coordinates to WGS84 (EPSG:4326)
        transform = QgsCoordinateTransform(canvasCrs, self.epsg4326, QgsProject.instance())

        # Transform the extent coordinates to EPSG:4326 (WGS84)
        bottom_left = transform.transform(extent.xMinimum(), extent.yMinimum())
        top_right = transform.transform(extent.xMaximum(), extent.yMaximum())

        # Create the bounding box string in WGS84 for the API call
        bounding_box = f"{bottom_left.y()},{bottom_left.x()},{top_right.y()},{top_right.x()}"

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            grid_data = self.w3w.getGridSection(bounding_box)

            # Check if the API response contains an error
            if 'error' in grid_data:
                error_code = grid_data['error']['code']
                error_message = grid_data['error']['message']
                iface.messageBar().pushMessage("what3words Error", 
                    f"Error fetching grid: {error_code} - {error_message}", level=Qgis.Warning, duration=5)
                return
            
            # Ensure that the grid layer exists
            self.ensureGridLayer()

            # Get the data provider for the grid layer
            pr = self.grid_layer.dataProvider()

            # Clear any existing features in the layer (to avoid duplicates)
            self.grid_layer.startEditing()
            pr.deleteFeatures([f.id() for f in self.grid_layer.getFeatures()])
            self.grid_layer.commitChanges()

            # Loop through the grid lines and add them as features to the layer
            for line in grid_data['lines']:
                point1 = QgsPoint(line['start']['lng'], line['start']['lat'])
                point2 = QgsPoint(line['end']['lng'], line['end']['lat'])

                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline([point1, point2]))
                # Set the south, west, north, and east attributes based on the bounding box
                feature.setAttributes([bottom_left.y(), bottom_left.x(), top_right.y(), top_right.x()])
                # Add the feature to the data provider
                pr.addFeature(feature)

            # Update the layer's extents and trigger a repaint
            self.grid_layer.updateExtents()
            self.applyGridSymbology()
            # Update last fetched extent
            self.last_grid_extent = current_extent

        except GeoCodeException as e:
            # Directly use the error message provided by GeoCodeException
            iface.messageBar().pushMessage("what3words", str(e), level=Qgis.Warning, duration=5)
        finally:
            QApplication.restoreOverrideCursor()

    def saveGridToLayer(self, grid_data, bottom_left, top_right):
        """
        Saves the grid data and bounding box (as south, west, north, east) to a vector layer in QGIS.
        """
        # Ensure the grid layer exists
        self.ensureGridLayer()

        # Get the data provider for the grid layer
        provider = self.grid_layer.dataProvider()

        # Convert bounding box into individual lat/lng values (south, west, north, east)
        bounds = {
            "south": bottom_left.y(),
            "west": bottom_left.x(),
            "north": top_right.y(),
            "east": top_right.x()
        }

        # Ensure the grid_layer has fields for south, west, north, east
        if not self.grid_layer.fields().indexOf('south') >= 0:
            provider.addAttributes([
                QgsField("south", QVariant.Double),
                QgsField("west", QVariant.Double),
                QgsField("north", QVariant.Double),
                QgsField("east", QVariant.Double)
            ])
            self.grid_layer.updateFields()  # Update layer's fields

        # Check if the same bounding box has already been added
        existing_features = [f for f in self.grid_layer.getFeatures()]
        for feature in existing_features:
            if (feature['south'] == bounds['south'] and feature['west'] == bounds['west'] and
                feature['north'] == bounds['north'] and feature['east'] == bounds['east']):
                # Skip adding the bounding box if it's already in the layer
                return

        # Add new features (grid lines) and the bounding box information to the grid layer
        for line in grid_data['lines']:
            feature = QgsFeature()

            # Create the LineString geometry for the grid line
            point1 = QgsPoint(line['start']['lng'], line['start']['lat'])
            point2 = QgsPoint(line['end']['lng'], line['end']['lat'])
            feature.setGeometry(QgsGeometry.fromPolyline([point1, point2]))

            # Set the attributes for the bounding box (south, west, north, east)
            feature.setAttributes([
                bounds['south'],
                bounds['west'],
                bounds['north'],
                bounds['east']
            ])

            # Add the feature to the layer
            provider.addFeature(feature)

        # Update the layer extents and repaint
        self.grid_layer.updateExtents()
        self.grid_layer.triggerRepaint()

    def ensureGridLayer(self):
        """
        Ensures that the grid layer exists. If it doesn't, this method recreates it.
        """
        # Check if the layer exists in the project
        if not self.grid_layer or not QgsProject.instance().mapLayersByName(self.grid_layer.name()):
            # The layer doesn't exist anymore or was deleted, recreate it
            self.grid_layer = QgsVectorLayer("LineString", "what3words Grid", "memory")
            
            # Define the attributes for the grid layer
            pr = self.grid_layer.dataProvider()
            pr.addAttributes([
                QgsField("south", QVariant.Double),
                QgsField("west", QVariant.Double),
                QgsField("north", QVariant.Double),
                QgsField("east", QVariant.Double)
            ])
            self.grid_layer.updateFields()

            QgsProject.instance().addMapLayer(self.grid_layer)
        else:
            # Reset the layer if it has been deleted manually
            layers = QgsProject.instance().mapLayersByName(self.grid_layer.name())
            if not layers:
                # Recreate the layer if it's not valid anymore
                self.grid_layer = QgsVectorLayer("LineString", "what3words Grid", "memory")
                QgsProject.instance().addMapLayer(self.grid_layer)

    def removeGridLayer(self):
        """
        Safely checks if the grid layer exists. If removed manually, prompt to save.
        """
        if self.grid_layer:
            layers = QgsProject.instance().mapLayersByName(self.grid_layer.name())
            if layers:
                # The grid layer still exists; don't remove it when disabling
                return
            else:
                # The grid layer has been manually removed
                iface.messageBar().pushMessage("Grid", "The grid layer was manually removed.", level=Qgis.Warning)
                self.grid_layer = None
        else:
            iface.messageBar().pushMessage("Grid", "No grid layer found to remove.", level=Qgis.Warning)

    def applyGridSymbology(self):
        """
        Applies symbology to the what3words grid layer based on whether a satellite or vector map is active.
        """
        satellite_keywords = ['satellite', 'google satellite', 'imagery', 'arcgis satellite', 'bing aerial', 'google satellite']
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
