# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

import os
import webbrowser

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QIcon, QAction

from qgis.core import QgsApplication

from what3words.maptool import W3WMapTool
from what3words.coorddialog import W3WCoordInputDialog
from what3words.apikey import apikey, askForApiKey

try:
    from processing.core.Processing import Processing
    from processingprovider.w3wprovider import W3WProvider
    processingOk = True
except:
    raise
    processingOk = False

class W3WTools:

    def __init__(self, iface):
        self.iface = iface

        try:
            from what3words.tests import testerplugin
            from qgistester.tests import addTestModule
            addTestModule(testerplugin, "what3words")
        except:
            pass

        self.mapTool = None
        if processingOk:
            self.provider = W3WProvider()

    def initGui(self):
        mapToolIcon = QIcon(os.path.join(os.path.dirname(__file__), "w3w.png"))
        self.toolAction = QAction(mapToolIcon, "what3words map tool",
                                     self.iface.mainWindow())
        self.toolAction.triggered.connect(self.setTool)
        self.toolAction.setCheckable(True)
        self.iface.addToolBarIcon(self.toolAction)
        self.iface.addPluginToMenu("what3words", self.toolAction)

        zoomToIcon = QIcon(':/images/themes/default/mActionZoomIn.svg')
        self.zoomToAction = QAction(zoomToIcon, "Zoom to 3 word address",
                                     self.iface.mainWindow())
        self.zoomToAction.triggered.connect(self.zoomTo)
        self.iface.addPluginToMenu("what3words", self.zoomToAction)

        self.apikeyAction = QAction("Set API key",
                                     self.iface.mainWindow())
        self.apikeyAction.triggered.connect(askForApiKey)
        self.iface.addPluginToMenu("what3words", self.apikeyAction)

        helpIcon = QgsApplication.getThemeIcon('/mActionHelpAPI.png')
        self.helpAction = QAction(helpIcon, "what3words Plugin Help", self.iface.mainWindow())
        self.helpAction.setObjectName("what3wordsHelp")
        self.helpAction.triggered.connect(lambda: webbrowser.open_new("file://" + os.path.join(os.path.dirname(__file__), "docs", "html", "index.html")))
        self.iface.addPluginToMenu("what3words", self.helpAction)

        self.iface.mapCanvas().mapToolSet.connect(self.unsetTool)

        self.zoomToDialog = W3WCoordInputDialog(self.iface.mapCanvas(), self.iface.mainWindow())
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()

        if processingOk:
            Processing.addProvider(self.provider)

    def zoomTo(self):
        if apikey() is None:
            return
        self.zoomToDialog.setApiKey(apikey())
        self.zoomToDialog.show()

    def unsetTool(self, tool):
        try:
            if not isinstance(tool, W3WMapTool):
                self.toolAction.setChecked(False)
        except:
            pass
            #ignore exceptions thrown when unloading plugin, since map tool class might not exist already

    def setTool(self):
        if apikey() is None:
            return
        if self.mapTool is None:
            self.mapTool = W3WMapTool(self.iface.mapCanvas())
        self.toolAction.setChecked(True)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def unload(self):
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
        self.iface.removeToolBarIcon(self.toolAction)
        self.iface.removePluginMenu("what3words", self.toolAction)
        self.iface.removePluginMenu("what3words", self.zoomToAction)
        self.iface.removePluginMenu("what3words", self.apikeyAction)
        self.iface.removeDockWidget(self.zoomToDialog)
        if processingOk:
            Processing.removeProvider(self.provider)

        try:
            from what3words.tests import testerplugin
            from qgistester.tests import removeTestModule
            removeTestModule(testerplugin, "what3words")
        except:
            pass
