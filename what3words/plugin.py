from __future__ import absolute_import

import os
import webbrowser
from builtins import object

from qgis.core import Qgis, QgsApplication, QgsProject
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface
from qgiscommons2.gui import (addAboutMenu, addHelpMenu, removeAboutMenu,
                              removeHelpMenu)
from qgiscommons2.gui.settings import addSettingsMenu, removeSettingsMenu
from qgiscommons2.settings import pluginSetting, readSettings

from what3words.coorddialog import W3WCoordInputDialog
from what3words.maptool import W3WMapTool
from what3words.processingprovider.w3wprovider import W3WProvider


class W3WTools(object):

    def __init__(self, iface):
        self.iface = iface
        self.grid_enabled = False  # New flag to keep track of grid state
        self.mapTool = None
        self.provider = W3WProvider()
        
        try:
            from qgistester.tests import addTestModule

            from what3words.tests import testerplugin
            addTestModule(testerplugin, "what3words")
        except:
            pass

        readSettings()

    def initGui(self):
        mapToolIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w.png"))
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

        # Add the grid toggle button
        gridIcon = QIcon(':/images/themes/default/mActionSnapToGrid.svg')
        self.gridToggleAction = QAction(gridIcon, "Toggle W3W Grid", self.iface.mainWindow())
        self.gridToggleAction.setCheckable(True)
        self.gridToggleAction.triggered.connect(self.toggleGrid)  # Connect to grid toggle method
        self.iface.addToolBarIcon(self.gridToggleAction)
        self.iface.addPluginToMenu("what3words", self.gridToggleAction)

        addSettingsMenu(
            "what3words", self.iface.addPluginToMenu)
        addHelpMenu(
            "what3words", self.iface.addPluginToMenu)
        addAboutMenu(
            "what3words", self.iface.addPluginToMenu)

        self.iface.mapCanvas().mapToolSet.connect(self.unsetTool)

        self.zoomToDialog = W3WCoordInputDialog(self.iface.mapCanvas(), self.iface.mainWindow())
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()

        QgsApplication.processingRegistry().addProvider(self.provider)

        try:
            from lessons import addGroup, addLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            addLessonsFolder(folder, "what3words")
        except:
            pass

    def toggleGrid(self, checked):
        """
        Toggles the What3words grid on and off.
        """
        if self.mapTool is None:
            self.mapTool = W3WMapTool(self.iface.mapCanvas())

        if checked:
            self.mapTool.enableGrid(True)
            self._showMessage("W3W Grid enabled.", Qgis.Info)
        else:
            self.mapTool.enableGrid(False)
            self._showMessage("W3W Grid disabled.", Qgis.Info)

    def showW3WGrid(self):
        """
        Method to trigger the What3words grid drawing.
        Calls fetchAndDrawW3WGrid from the map tool if it's available.
        """
        apikey = pluginSetting("apiKey")
        if apikey is None or apikey == "":
            self._showMessage('what3words API key is not set. Please set it and try again.', QgsMessageBar.WARNING)
            return

        # Check if the map tool exists and if so, call the grid drawing method
        if self.mapTool is None:
            self.mapTool = W3WMapTool(self.iface.mapCanvas())
        
        # Call the method to draw the grid
        self.mapTool.fetchAndDrawW3WGrid()

    def zoomTo(self):
        apikey = pluginSetting("apiKey")
        if apikey is None or apikey == "":
            self._showMessage('what3words API key is not set. Please set it and try again.', QgsMessageBar.WARNING)
            return
        self.zoomToDialog.setApiKey(apikey)
        self.zoomToDialog.show()

    def unsetTool(self, tool):
        try:
            if not isinstance(tool, W3WMapTool):
                self.toolAction.setChecked(False)
        except:
            # ignore exceptions thrown when unloading plugin, since
            # map tool class might not exist already
            pass

    def setTool(self):
        apikey = pluginSetting("apiKey")
        if apikey is None or apikey == "":
            self._showMessage('what3words API key is not set. Please set it and try again.', Qgis.Warning)
            return
        if self.mapTool is None:
            self.mapTool = W3WMapTool(self.iface.mapCanvas())
        self.toolAction.setChecked(True)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def unload(self):
        if self.mapTool and self.mapTool.grid_enabled:
            self.mapTool.enableGrid(False)

        self.iface.removeToolBarIcon(self.gridToggleAction)
        self.iface.removePluginMenu("what3words", self.gridToggleAction)
        
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
        self.iface.removeToolBarIcon(self.toolAction)
        self.iface.removePluginMenu("what3words", self.toolAction)
        self.iface.removePluginMenu("what3words", self.zoomToAction)        

        removeSettingsMenu("what3words")
        removeHelpMenu("what3words")
        removeAboutMenu("what3words")

        self.iface.removeDockWidget(self.zoomToDialog)

        QgsApplication.processingRegistry().removeProvider(self.provider)

        try:
            from qgistester.tests import removeTestModule

            from what3words.tests import testerplugin
            removeTestModule(testerplugin, "what3words")
        except:
            pass

        try:
            from lessons import removeLessonsFolder
            folder = os.path.join(pluginPath, '_lessons')
            removeLessonsFolder(folder)
        except:
            pass

    def _showMessage(self, message, level=Qgis.Info):
        iface.messageBar().pushMessage(
            message, level, iface.messageTimeout())
