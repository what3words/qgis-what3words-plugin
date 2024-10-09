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

from what3words.coorddialog import W3WCoordInputDialog  # Import the coord dialog
from what3words.maptool import W3WMapTool
from what3words.grid import W3WGridManager
from what3words.processingprovider.w3wprovider import W3WProvider


class W3WTools(object):

    def __init__(self, iface):
        self.iface = iface
        self.gridManager = None  # Initialize for grid management
        self.mapTool = None
        self.provider = W3WProvider()
        self.zoomToDialog = None  # To manage the dialog window
        
        try:
            from qgistester.tests import addTestModule

            from what3words.tests import testerplugin
            addTestModule(testerplugin, "what3words")
        except:
            pass

        readSettings()

    def initGui(self):
        # Add map tool button
        mapToolIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w.png"))
        self.toolAction = QAction(mapToolIcon, "what3words map tool", self.iface.mainWindow())
        self.toolAction.triggered.connect(self.setTool)
        self.toolAction.setCheckable(True)
        self.iface.addToolBarIcon(self.toolAction)
        self.iface.addPluginToMenu("what3words", self.toolAction)

        # Add zoom to what3words address button
        zoomToIcon = QIcon(':/images/themes/default/mActionZoomIn.svg')
        self.zoomToAction = QAction(zoomToIcon, "Zoom to what3words address", self.iface.mainWindow())
        self.zoomToAction.triggered.connect(self.showW3WCoordInputDialog)
        self.iface.addToolBarIcon(self.zoomToAction)
        self.iface.addPluginToMenu("what3words", self.zoomToAction)

        # Add grid toggle button with dynamic text updates
        gridIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "grid-red.svg"))
        self.gridToggleAction = QAction(gridIcon, "View Grid", self.iface.mainWindow())
        self.gridToggleAction.setCheckable(True)
        self.gridToggleAction.toggled.connect(self.toggleGrid)
        self.iface.addToolBarIcon(self.gridToggleAction)
        self.iface.addPluginToMenu("what3words", self.gridToggleAction)

        # Add the dock widget for zooming to w3w
        self.zoomToDialog = W3WCoordInputDialog(self.iface.mapCanvas(), self.iface.mainWindow())
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()

        # Add settings, help, and about menus
        addSettingsMenu("what3words", self.iface.addPluginToMenu)
        addHelpMenu("what3words", self.iface.addPluginToMenu)
        addAboutMenu("what3words", self.iface.addPluginToMenu)

        # Connect map tool set/unset event
        self.iface.mapCanvas().mapToolSet.connect(self.unsetTool)

        # Register the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

        try:
            from lessons import addGroup, addLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            addLessonsFolder(folder, "what3words")
        except:
            pass

    def showW3WCoordInputDialog(self):
        """
        Shows the 'Zoom to what3words address' dock widget.
        """
        if self.zoomToDialog.isHidden():
            self.zoomToDialog.show()
        else:
            self.zoomToDialog.hide()

    def toggleGrid(self, checked):
        """
        Toggles the What3words grid on and off and updates the button text.
        The grid is shown or hidden immediately after the button is clicked.
        """
        if self.gridManager is None:
            self.gridManager = W3WGridManager(self.iface.mapCanvas())

        if checked:
            self.gridManager.enableGrid(True)
            self.gridToggleAction.setText("Hide Grid")
            self._showMessage("W3W Grid enabled.", Qgis.Info)
        else:
            self.gridManager.enableGrid(False)
            self.gridToggleAction.setText("View Grid")
            self._showMessage("W3W Grid disabled.", Qgis.Info)

    def setTool(self):
        """
        Activates the what3words map tool for converting map clicks to 3-word addresses.
        """
        apikey = pluginSetting("apiKey")
        if apikey is None or apikey == "":
            self._showMessage('what3words API key is not set. Please set it and try again.', Qgis.Warning)
            return
        if self.mapTool is None:
            self.mapTool = W3WMapTool(self.iface.mapCanvas())
        self.toolAction.setChecked(True)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def unsetTool(self, tool):
        """
        Unchecks the map tool action if another map tool is set.
        """
        try:
            if not isinstance(tool, W3WMapTool):
                self.toolAction.setChecked(False)
        except:
            pass

    def unload(self):
        """
        Cleans up all components when the plugin is unloaded.
        """
        if self.gridManager and self.gridManager.grid_enabled:
            self.gridManager.enableGrid(False)

        self.iface.removeToolBarIcon(self.gridToggleAction)
        self.iface.removePluginMenu("what3words", self.gridToggleAction)
        
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
        self.iface.removeToolBarIcon(self.toolAction)
        self.iface.removePluginMenu("what3words", self.toolAction)
        self.iface.removePluginMenu("what3words", self.zoomToAction)

        self.iface.removeDockWidget(self.zoomToDialog)

        removeSettingsMenu("what3words")
        removeHelpMenu("what3words")
        removeAboutMenu("what3words")

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
