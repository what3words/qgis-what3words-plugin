# -*- coding: utf-8 -*-

# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.

import os

from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsProcessingProvider
 
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from what3words.processingprovider.add3wordsfield import Add3WordsFieldAlgorithm
from what3words.processingprovider.addgeomfield import Add3WordsGeomFieldAlgorithm
from what3words.processingprovider.generatew3wgrid import GenerateW3WGridAlgorithm
from what3words.processingprovider.convertw3wlanguage import ConvertWhat3WordsLanguageAlgorithm

pluginPath = os.path.split(os.path.dirname(__file__))[0]

class W3WProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(Setting(self.name(), 'ACTIVATE_W3W',
                                            'Activate', True))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        QgsProcessingProvider.unload(self)

    def isActive(self):
        """Return True if the provider is activated and ready to run algorithms"""
        return ProcessingConfig.getSetting('ACTIVATE_W3W')

    def setActive(self, active):
        ProcessingConfig.setSettingValue('ACTIVATE_W3W', active)

    def id(self):
        return 'what3words'

    def name(self):        
        return 'what3words Tools'

    def icon(self):        
        return QIcon(os.path.join(pluginPath, 'icons', 'w3w.png'))

    def loadAlgorithms(self):
        for alg in [Add3WordsFieldAlgorithm()]:
            self.addAlgorithm(alg)
        for alg in [Add3WordsGeomFieldAlgorithm()]:
            self.addAlgorithm(alg)
        for alg in [GenerateW3WGridAlgorithm()]:
            self.addAlgorithm(alg)
        for alg in [ConvertWhat3WordsLanguageAlgorithm()]:
            self.addAlgorithm(alg)
