# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QIcon
from qgis.core import *
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from what3words.w3w import what3words
from what3words.apikey import apikey

class Add3WordsFieldAlgorithm(GeoAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def processAlgorithm(self, progress):
        apik = apikey(False)
        if apik is None:
             raise GeoAlgorithmExecutionException("what3words API key is not defined")
        w3w = what3words(apikey=apik)
        filename = self.getParameterValue(self.INPUT)
        layer = dataobjects.getObjectFromUri(filename)
        vprovider = layer.dataProvider()
        fields = vprovider.fields()
        caps = layer.dataProvider().capabilities()
        if not (caps & QgsVectorDataProvider.AddAttributes):
            raise GeoAlgorithmExecutionException("The selected layer does not support adding new attributes.")

        idxField = fields.indexFromName("3WordAddr")
        if idxField == -1:
            vprovider.addAttributes([QgsField("3WordAddr", QVariant.String)])
            layer.updateFields()
            idxField = len(fields)
        nFeat = layer.featureCount()
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(layer.crs(), epsg4326)

        for i, feat in enumerate(layer.getFeatures()):
            progress.setPercentage(int(100 * i / nFeat))
            pt = feat.geometry().vertexAt(0)
            try:
                pt4326 = transform.transform(pt.x(), pt.y())
                threeWords = self.w3w.reverseGeocode(pt4326.y(), pt4326.x())["words"]

            except Exception,e :
                threeWords = ""
            layer.dataProvider().changeAttributeValues({feat.id() : {idxField: threeWords}})

        self.setOutputValue(self.OUTPUT, filename)

    def defineCharacteristics(self):
        self.name = 'Add 3 word address field to points layer'
        self.i18n_name = self.name
        self.group = 'what3words tools'
        self.i18n_group = self.group
        self.addParameter(ParameterVector(self.INPUT,
                                          'Input layer', [ParameterVector.VECTOR_TYPE_POINT]))
        self.addOutput(OutputVector(self.OUTPUT, 'Output', True))

    def getIcon(self):
        return QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), "w3w.png"))
