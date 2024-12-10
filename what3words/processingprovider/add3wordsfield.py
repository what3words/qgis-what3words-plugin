# -*- coding: utf-8 -*-

# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.


import os

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsProcessingException,
                       QgsCoordinateTransform,
                       QgsField,
                       QgsProject,
                       QgsFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm

from what3words.utils import get_w3w_instance


pluginPath = os.path.split(os.path.dirname(__file__))[0]

class Add3WordsFieldAlgorithm(QgisAlgorithm):
    """
    This algorithm adds a what3words address field to each feature in the input layer.
    Attributes:
        INPUT (str): The name of the input parameter for the input layer.
        OUTPUT (str): The name of the output parameter for the output layer.
    Methods:
        __init__(): Initializes the algorithm.
        initAlgorithm(config=None): Defines the inputs and outputs of the algorithm.
        name(): Returns the unique name of the algorithm.
        displayName(): Returns the display name of the algorithm.
        processAlgorithm(parameters, context, feedback): Processes the input layer and adds a what3words address field to each feature.
    """

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    # def group(self):
    #     return self.tr('what3words')

    # def groupId(self):
    #     return 'w3w'

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Input point vector layer')))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,
                                                            self.tr('Output')))

    def name(self):
        return 'addw3wfield'

    def displayName(self):
        return self.tr('Add what3words field to layer')
    
    def helpString(self):
        return """
        <h1>Add what3words Field</h1>
        <p>This tool adds a new field to the input layer containing the <b>what3words</b> address of each feature's centroid.</p>
        <h3>Parameters:</h3>
        <ul>
          <li><b>Input layer:</b> The vector layer containing the features to process.</li>
          <li><b>Output layer:</b> The resulting layer with the added <code>what3words</code> field.</li>
        </ul>
        <h3>Usage Example:</h3>
        <p>After running the tool, a new field named <code>what3words</code> will be added to the attribute table of the output layer, containing the what3words addresses for each feature's centroid.</p>
        <h3>Notes:</h3>
        <ul>
          <li>The API key must be set in the plugin settings.</li>
          <li>The input layer must have a valid CRS.</li>
        </ul>
        """

    def helpUrl(self):
        return "https://developer.what3words.com/tools/gis-extensions/qgis"


    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)        
        fields = source.fields()
        field = QgsField("what3words", QVariant.String)
        fields.append(field)

        try:
            w3w = get_w3w_instance()  # Use centralized function to get API instance
        except ValueError as e:
            raise QgsProcessingException(f"Error initializing what3words API: {str(e)}")
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                            fields, source.wkbType(), source.sourceCrs())

        features = source.getFeatures()
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(source.sourceCrs(), epsg4326, QgsProject.instance())
            
        for current, feat in enumerate(features):
            if feedback.isCanceled():
                break

            feedback.setProgress(int(current * total))
            attrs = feat.attributes()
            pt = feat.geometry().centroid().asPoint()
            try:
                pt4326 = transform.transform(pt.x(), pt.y())
                threeWords = w3w.convertTo3wa(pt4326.y(), pt4326.x())["words"]
            except Exception as e:
                feedback.pushDebugInfo("Failed to retrieve what3words address for feature {}:\n{}".format(feat.id(), str(e)))
                threeWords = ""

            attrs.append(threeWords)
            feat.setAttributes(attrs)
            sink.addFeature(feat, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}
