# -*- coding: utf-8 -*-

import os
from qgis.PyQt.QtCore import QVariant
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFeatureSink,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsGeometry,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsProcessingException,
    QgsPointXY,
    QgsFeatureSink
)
from what3words.utils import get_w3w_instance


class GenerateW3WGridAlgorithm(QgisAlgorithm):
    """
    This algorithm generates a grid of `what3words` squares for a specific bounding box.
    """

    EXTENT = 'EXTENT'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def name(self):
        return 'generatew3wgrid'

    def displayName(self):
        return self.tr('Generate what3words Grid')
    
    def shortHelpString(self):
        """
        Returns a detailed help string for the algorithm.
        """
        return self.tr("""
        This tool generates a grid of what3words lines for a specified bounding box.
        <h3>Inputs:</h3>
        <ul>
          <li><b>Bounding Box:</b> Specify the extent for which the grid will be created.</li>
        </ul>
        <h3>Output:</h3>
        <ul>
          <li>A GeoJSON layer of lines representing what3words grid sections with attributes for the south, west, north, and east coordinates of each line.</li>
        </ul>
        <h3>Notes:</h3>
        <ul>
          <li>The bounding box will be split into smaller areas, with up to 10 API calls per area.</li>
          <li>An API key must be configured in the plugin settings.</li>
          <li>Input coordinates will be transformed to EPSG:4326 (WGS84) if they are in a different CRS.</li>
        </ul>
        """)
    
    def helpUrl(self):
        return "https://developer.what3words.com/tools/gis-extensions/qgis"


    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                self.tr('Bounding Box'),
                defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output GeoJSON Layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # Retrieve the extent parameter
        extent = self.parameterAsExtent(parameters, self.EXTENT, context)

        # Check API key and initialize `what3words`
        try:
            w3w = get_w3w_instance()
        except Exception as e:
            raise QgsProcessingException(f"Error initializing what3words API: {str(e)}")

        # Transform the input extent to WGS84 if needed
        project_crs = QgsProject.instance().crs()
        wgs84_crs = QgsCoordinateReferenceSystem('EPSG:4326')
        if project_crs != wgs84_crs:
            feedback.pushInfo(f"Transforming coordinates from {project_crs.authid()} to WGS84 (EPSG:4326)")
            transform = QgsCoordinateTransform(project_crs, wgs84_crs, QgsProject.instance())
            min_point = transform.transform(extent.xMinimum(), extent.yMinimum())
            max_point = transform.transform(extent.xMaximum(), extent.yMaximum())
            bbox = (min_point.x(), min_point.y(), max_point.x(), max_point.y())
        else:
            bbox = (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())

        # Output layer fields
        fields = QgsFields()
        fields.append(QgsField("south", QVariant.Double))
        fields.append(QgsField("west", QVariant.Double))
        fields.append(QgsField("north", QVariant.Double))
        fields.append(QgsField("east", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            wgs84_crs
        )

        # Function to split bounding box into smaller areas
        def split_bbox_into_areas(bbox, max_tiles=10, tile_size=0.036):  # Approx 4km in degrees
            areas = []
            min_x, min_y, max_x, max_y = bbox

            x = min_x
            while x < max_x:
                y = min_y
                while y < max_y:
                    # Create an area
                    area_x_max = min(x + tile_size * max_tiles**0.5, max_x)
                    area_y_max = min(y + tile_size * max_tiles**0.5, max_y)
                    areas.append((x, y, area_x_max, area_y_max))
                    y += tile_size * max_tiles**0.5
                x += tile_size * max_tiles**0.5
            return areas

        # Split the bounding box into areas limited to 10 API calls
        areas = split_bbox_into_areas(bbox)

        feedback.pushInfo(f"Total areas to process: {len(areas)}")

        # Iterate through each area and call the `what3words` API
        total = 100.0 / len(areas) if areas else 1
        for current, area in enumerate(areas):
            if feedback.isCanceled():
                break

            # Retrieve grid section from API
            try:
                response = w3w.getGridSection(f"{area[1]},{area[0]},{area[3]},{area[2]}")
                if 'lines' not in response:
                    raise QgsProcessingException(f"No grid data returned for area: {area}")
            except Exception as e:
                feedback.pushDebugInfo(f"Failed to retrieve grid for area {area}: {str(e)}")
                continue

            # Process lines
            for line in response['lines']:
                start = line['start']
                end = line['end']
                try:
                    # Form a line geometry
                    line_geom = QgsGeometry.fromPolylineXY([
                        QgsPointXY(start['lng'], start['lat']),
                        QgsPointXY(end['lng'], end['lat'])
                    ])

                    # Create a new feature with lat/lng attributes
                    feature = QgsFeature(fields)
                    feature.setGeometry(line_geom)
                    feature.setAttributes([
                        start['lat'],  # South latitude
                        start['lng'],  # West longitude
                        end['lat'],    # North latitude
                        end['lng']     # East longitude
                    ])
                    sink.addFeature(feature, QgsFeatureSink.FastInsert)
                except Exception as e:
                    feedback.pushDebugInfo(f"Error processing line: {str(e)}")
                    continue

            # Update progress
            feedback.setProgress(int(current * total))

        feedback.pushInfo("Grid generation complete.")
        return {self.OUTPUT: dest_id}