# -*- coding: utf-8 -*-

# (c) 2024 Your Name or Company
# This code is licensed under the GPL 2.0 license.

import os
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsFeatureSink,
    QgsField,
    QgsProcessingParameterField,
    QgsFeature,
    QgsProcessingException,
)
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm

from what3words.utils import get_w3w_instance

class ConvertWhat3WordsLanguageAlgorithm(QgisAlgorithm):
    """
    Translates what3words addresses in a given field to a target language.
    """

    INPUT = 'INPUT'
    WHAT3WORDS_FIELD = 'WHAT3WORDS_FIELD'
    LANGUAGE = 'LANGUAGE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        # Input vector layer
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input vector layer')
            )
        )
        # Field containing what3words addresses
        self.addParameter(
            QgsProcessingParameterField(
                self.WHAT3WORDS_FIELD,
                self.tr('What3Words field'),
                parentLayerParameterName=self.INPUT
            )
        )
        # Language selection
        w3w = get_w3w_instance()
        languages = self.get_supported_languages(w3w)
        self.addParameter(
            QgsProcessingParameterEnum(
                self.LANGUAGE,
                self.tr('Target Language'),
                languages,
                defaultValue=0
            )
        )
        # Output layer
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output')
            )
        )

    def name(self):
        return 'convertw3wlanguage'

    def displayName(self):
        return self.tr('Convert what3words addresses language')

    def shortHelpString(self):
        return self.tr("""
            This tool converts the language of existing what3words addresses in a specified field to another language 
            and adds a new field to the output layer with the converted addresses.

            <h3>Parameters:</h3>
            <ul>
              <li><b>Input vector layer:</b> The layer containing the what3words addresses.</li>
              <li><b>What3Words field:</b> The field containing the what3words addresses to convert.</li>
              <li><b>Target Language:</b> The desired language for the what3words addresses.</li>
              <li><b>Output layer:</b> The resulting layer with the new field containing the converted what3words addresses.</li>
            </ul>

            <h3>Notes:</h3>
            <ul>
              <li>The API key must be configured in the plugin settings.</li>
              <li>Only valid what3words addresses will be converted.</li>
            </ul>
        """)

    def helpUrl(self):
        return "https://developer.what3words.com/tools/gis-extensions/qgis"

    def get_supported_languages(self, w3w_instance):
        """
        Retrieve supported languages from the what3words API.

        :param w3w_instance: Configured what3words API instance.
        :return: List of supported language names.
        """
        try:
            languages = w3w_instance.getLanguages()
            return [lang['name'] for lang in languages['languages']]
        except Exception as e:
            raise QgsProcessingException(f"Failed to retrieve supported languages: {str(e)}")

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        w3w_field = self.parameterAsString(parameters, self.WHAT3WORDS_FIELD, context)
        target_language_index = self.parameterAsInt(parameters, self.LANGUAGE, context)

        try:
            w3w = get_w3w_instance()
            languages = w3w.getLanguages()
            target_language_code = languages['languages'][target_language_index]['code']
        except Exception as e:
            raise QgsProcessingException(f"Error retrieving target language: {str(e)}")

        # Define fields for the output layer
        fields = source.fields()
        converted_field_name = f"{w3w_field}_converted"
        converted_field = QgsField(converted_field_name, QVariant.String)
        fields.append(converted_field)

        # Initialize output layer sink
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                            fields, source.wkbType(), source.sourceCrs())

        features = source.getFeatures()
        total_features = source.featureCount()

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            original_w3w = feature[w3w_field]
            converted_w3w = None
            try:
                if original_w3w and original_w3w.strip():
                    # Fetch the coordinates of the original what3words address
                    original_coords = w3w.convertToCoordinates(original_w3w.strip())
                    lat = original_coords['coordinates']['lat']
                    lon = original_coords['coordinates']['lng']

                    # Convert the address to the target language
                    converted_result = w3w.convertTo3wa(lat, lon, language=target_language_code)
                    converted_w3w = converted_result['words']
            except Exception as e:
                feedback.pushDebugInfo(f"Failed to convert what3words address '{original_w3w}': {str(e)}")

            # Add converted what3words address to the new field
            new_feature = QgsFeature(feature)
            new_feature.setFields(fields, False)
            new_feature.setAttribute(converted_field_name, converted_w3w)  # Set converted value
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

            # Update progress
            feedback.setProgress(int((current / total_features) * 100))

        return {self.OUTPUT: dest_id}