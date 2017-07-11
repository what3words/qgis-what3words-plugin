# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
from qgis.PyQt.QtGui import QIcon

from processing.core.AlgorithmProvider import AlgorithmProvider

from what3words.processingprovider.add3wordsfield import Add3WordsFieldAlgorithm

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class W3WProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = True

        # Load algorithms
        self.alglist = [Add3WordsFieldAlgorithm()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    def getName(self):
        return 'what3words'

    def getDescription(self):
        return 'what3words tools'

    def getIcon(self):
        return QIcon(os.path.join(pluginPath, "icons", "w3w.png"))

    def _loadAlgorithms(self):
        self.algs = self.alglist
