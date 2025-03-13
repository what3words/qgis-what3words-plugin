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
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterEnum)
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm

from what3words.utils import get_w3w_instance


class Add3WordsFieldAlgorithm(QgisAlgorithm):
    """
    This algorithm adds a what3words address field to each feature in the input layer.
    """

    INPUT = 'INPUT'
    LANGUAGE = 'LANGUAGE'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.language_mapping = {}

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, self.tr('Input point vector layer')))
        
        # Initialize languages and create LANGUAGE parameter
        w3w = get_w3w_instance()
        language_names = self.get_supported_language_names(w3w)
        self.addParameter(QgsProcessingParameterEnum(
            self.LANGUAGE,
            self.tr('Select Language'),
            language_names,
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Output')))

    def name(self):
        return 'addw3wfield'

    def displayName(self):
        return self.tr('Add what3words field to layer')
    
    def shortHelpString(self):
        return self.tr("""
        <p>This tool adds a new field to the input layer containing the <i>what3words address</i> of each feature's centroid.</p>
        <h3>Parameters:</h3>
        <ul>
            <li><b>Input layer:</b> The vector point layer containing the features to process.</li>
            <li><b>Language:</b> The language in which the what3words address should be generated.</li>
            <li><b>Output layer:</b> The resulting layer with the added <code>what3words</code> field.</li>
        </ul>
        <h3>Usage Example:</h3>
        <p>After running the tool, a new field named <b><code>what3words</code></b> will be added to the attribute table of the output layer, containing the what3words addresses for each feature's centroid.</p>
        <h3>Notes:</h3>
        <ul>
          <li>The API key must be set in the plugin settings.</li>
          <li>The input layer must have a valid CRS.</li>
        </ul>
        """)

    def helpUrl(self):
        return "https://developer.what3words.com/tools/gis-extensions/qgis"
    
    def get_supported_language_names(self, w3w_instance):
        """
        Retrieve supported languages from the what3words API.

        :param w3w_instance: Configured what3words API instance.
        :return: List of supported language names.
        """
        try:
            languages = w3w_instance.getLanguages()
            self.language_mapping = {lang["name"]: lang["code"] for lang in languages["languages"]}
            return list(self.language_mapping.keys())
        except Exception as e:
            raise QgsProcessingException(f"Failed to retrieve supported languages: {str(e)}")

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)   
        selected_language_index = self.parameterAsInt(parameters, self.LANGUAGE, context)

        # Map selected language name to its code
        try:
            selected_language_name = list(self.language_mapping.keys())[selected_language_index]
            selected_language_code = self.language_mapping[selected_language_name]
        except (IndexError, KeyError) as e:
            raise QgsProcessingException(f"Invalid language selection: {str(e)}")
     
        fields = source.fields()
        field = QgsField("what3words", QVariant.String)
        fields.append(field)
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                            fields, source.wkbType(), source.sourceCrs())

        features = source.getFeatures()
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(source.sourceCrs(), epsg4326, QgsProject.instance())
        w3w = get_w3w_instance()
            
        for current, feat in enumerate(features):
            if feedback.isCanceled():
                break

            feedback.setProgress(int(current * total))
            attrs = feat.attributes()
            pt = feat.geometry().centroid().asPoint()
            try:
                pt4326 = transform.transform(pt.x(), pt.y())
                threeWords = w3w.convertTo3wa(pt4326.y(), pt4326.x(), language=selected_language_code)["words"]
            except Exception as e:
                feedback.pushDebugInfo("Failed to retrieve what3words address for feature {}:\n{}".format(feat.id(), str(e)))
                threeWords = ""

            attrs.append(threeWords)
            feat.setAttributes(attrs)
            sink.addFeature(feat, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}
