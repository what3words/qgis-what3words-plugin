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

from what3words.w3w import what3words
from qgiscommons2.settings import pluginSetting

pluginPath = os.path.split(os.path.dirname(__file__))[0]

class Add3WordsGeomFieldAlgorithm(QgisAlgorithm):

    INPUT = 'INPUT'
    W3WFIELD = 'WHAT3WORDS ADDRESS'
    OUTPUT = 'OUTPUT'

    def group(self):
        return self.tr('what3words')

    def groupId(self):
        return 'w3w'

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMapLayer(self.INPUT, self.tr('Input layer')))
        self.addParameter(QgsProcessingParameterField(self.W3WFIELD, self.tr('what3words address field'),
                '',
                self.INPUT))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,
                                                            self.tr('Output')))

    def name(self):
        return 'addw3wgeomfield'

    def displayName(self):
        return self.tr('Geocode what3words address layer')

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)  
        w3wField = self.parameterAsString(
        parameters,
        self.W3WFIELD,
        context)       
        fields = source.fields()
        idxFieldId = fields.indexFromName(w3wField)

        apiKey = pluginSetting("apiKey")
        addressLanguage = pluginSetting("addressLanguage")
        w3w = what3words(apikey=apiKey,addressLanguage=addressLanguage)
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
                data = w3w.convertToCordinates(threewa)
                lat = data["coordinates"]["lat"]
                lng = data["coordinates"]["lng"]
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lng,lat ))) 
            except Exception as e:
                feedback.setDebugInfo("Failed to retrieve w3w address for feature {}:\n{}".format(feat.id(), str(e)))
                threeWords = ""
            
               
            feat.setAttributes(attrs)
            sink.addFeature(feat, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}
