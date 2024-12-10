# -*- coding: utf-8 -*-

# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.


import os

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsProcessingException,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsField,
                       QgsProject,
                       QgsFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMapLayer,
                       QgsWkbTypes,
                       QgsGeometry,
                       QgsProcessingParameterField,
                       QgsPointXY,
                       QgsProcessingParameterFeatureSink)
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm

from what3words.utils import get_w3w_instance
from qgiscommons2.settings import pluginSetting

pluginPath = os.path.split(os.path.dirname(__file__))[0]

class Add3WordsGeomFieldAlgorithm(QgisAlgorithm):

    INPUT = 'INPUT'
    W3WFIELD = 'WHAT3WORDS ADDRESS'
    OUTPUT = 'OUTPUT'

    # def group(self):
    #     return self.tr('what3words')

    # def groupId(self):
    #     return 'w3w'

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMapLayer(self.INPUT, self.tr('Input CSV file')))
        self.addParameter(QgsProcessingParameterField(self.W3WFIELD, self.tr('what3words address field'),
                '',
                self.INPUT))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,
                                                            self.tr('Output')))

    def name(self):
        return 'addw3wgeomfield'

    def displayName(self):
        return self.tr('Geocode what3words address layer')
    
    def helpString(self):
        """
        Returns a detailed help string for the algorithm.
        """
        return """
        <h1>Geocode what3words Address Layer</h1>
        <p>This algorithm geocodes a CSV file using a field containing <b>what3words</b> addresses. 
        The output is a new point layer with geometries corresponding to the geocoded 3 word addresses.</p>

        <h3>Parameters:</h3>
        <ul>
          <li><b>CSV file:</b> The input vector layer containing features with what3words addresses.</li>
          <li><b>What3words address field:</b> The field in the input layer that contains the what3words addresses.</li>
          <li><b>Output layer:</b> The resulting layer with point geometries based on the geocoded what3words addresses.</li>
        </ul>

        <h3>Notes:</h3>
        <ul>
          <li>The field containing what3words addresses must be specified and valid.</li>
          <li>An API key must be configured in the plugin settings.</li>
          <li>All geometries are transformed to EPSG:4326 (WGS84) for consistency.</li>
          <li>Features with invalid or missing what3words addresses will not be geocoded and will generate debug information.</li>
        </ul>
        """
    
    def helpUrl(self):
        return "https://developer.what3words.com/tools/gis-extensions/qgis"

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)  
        w3wField = self.parameterAsString(
        parameters,
        self.W3WFIELD,
        context)       
        fields = source.fields()
        idxFieldId = fields.indexFromName(w3wField)

        try:
            w3w = get_w3w_instance()  # Use centralized function to get API instance
        except ValueError as e:
            raise QgsProcessingException(f"Error initializing what3words API: {str(e)}")

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.Point, QgsCoordinateReferenceSystem('EPSG:4326'))
        features = source.getFeatures()
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(source.sourceCrs(), epsg4326, QgsProject.instance())

        for current, feat in enumerate(features):
            if feedback.isCanceled():
                break

            feedback.setProgress(int(current * total))
            attrs = feat.attributes()
            threewa = attrs[idxFieldId]
            try:
                data = w3w.convertToCoordinates(threewa)
                lat = data["coordinates"]["lat"]
                lng = data["coordinates"]["lng"]
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lng,lat ))) 
            except Exception as e:
                feedback.pushDebugInfo("Failed to retrieve w3w address for feature {}:\n{}".format(feat.id(), str(e)))
                threeWords = ""
            
               
            feat.setAttributes(attrs)
            sink.addFeature(feat, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}
