from __future__ import absolute_import

import os
import webbrowser
from builtins import object

from qgis.core import Qgis, QgsApplication, QgsProject
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.utils import iface
from qgiscommons2.gui import (addAboutMenu, addHelpMenu, removeAboutMenu,
                              removeHelpMenu)
from qgiscommons2.gui.settings import addSettingsMenu, removeSettingsMenu, openSettingsDialog
from qgiscommons2.settings import pluginSetting, readSettings

from what3words.coorddialog import W3WCoordInputDialog 
from what3words.maptool import W3WMapTool
from what3words.grid import W3WGridManager
from what3words.w3wfunctions import register_w3w_functions, unregister_w3w_functions 
from what3words.processingprovider.w3wprovider import W3WProvider


class W3WTools(object):

    def __init__(self, iface):
        self.iface = iface
        self.gridManager = None  
        self.mapTool = None
        self.provider = W3WProvider()
        self.zoomToDialog = None 
        register_w3w_functions() 
        
        try:
            from qgistester.tests import addTestModule
            from what3words.tests import testerplugin
            addTestModule(testerplugin, "what3words")
        except:
            pass

        readSettings()

    def initGui(self):

        # Add map tool button
        if not hasattr(self, 'toolAction'):
            mapToolIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w_marker.svg"))
            self.toolAction = QAction(mapToolIcon, "View what3words address", self.iface.mainWindow())
            self.toolAction.triggered.connect(self.toggleTool)
            self.toolAction.setCheckable(True)
            self.iface.addToolBarIcon(self.toolAction)
            self.iface.addPluginToMenu("what3words", self.toolAction)

        # Add zoom to what3words address button
        if not hasattr(self, 'zoomToAction'):
            zoomToIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w_search.svg"))
            self.zoomToAction = QAction(zoomToIcon, "Zoom to what3words address", self.iface.mainWindow())
            self.zoomToAction.triggered.connect(self.showW3WCoordInputDialog)
            self.zoomToAction.setCheckable(True)
            self.iface.addToolBarIcon(self.zoomToAction)
            self.iface.addPluginToMenu("what3words", self.zoomToAction)

        # Add grid toggle button with dynamic text updates
        if not hasattr(self, 'gridToggleAction'):
            gridIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "grid_red.svg"))
            self.gridToggleAction = QAction(gridIcon, "View Grid", self.iface.mainWindow())
            self.gridToggleAction.setCheckable(True)
            self.gridToggleAction.toggled.connect(self.toggleGrid)
            self.iface.addToolBarIcon(self.gridToggleAction)
            self.iface.addPluginToMenu("what3words", self.gridToggleAction)

        # Add settings button to toolbar
        if not hasattr(self, 'settingsAction'):
            self.settingsAction = QAction(QgsApplication.getThemeIcon('/mActionOptions.svg'), "Settings",iface.mainWindow())
            self.settingsAction.triggered.connect(self.showSettingsDialog)
            self.iface.addToolBarIcon(self.settingsAction)
            self.iface.addPluginToMenu("what3words", self.settingsAction)

        # Add the dock widget for zooming to w3w
        self.zoomToDialog = W3WCoordInputDialog(self.iface.mapCanvas(), self.iface.mainWindow())
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()

        # Add settings, help, and about menus
        addHelpMenu("what3words", self.iface.addPluginToMenu)
        addAboutMenu("what3words", self.iface.addPluginToMenu)

        # Register the processing provider
        QgsApplication.processingRegistry().addProvider(self.provider)

        try:
            from lessons import addGroup, addLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            addLessonsFolder(folder, "what3words")
        except:
            pass
    
    def showSettingsDialog(self):
        """
        Opens the settings dialog.
        """
        openSettingsDialog("what3words")

    def warningAPIsettings(self):
        apikey = pluginSetting("apiKey")
        if not apikey:
            self._showMessage('what3words API key is not set. Please set it and try again.', Qgis.Warning)
            return

    def showW3WCoordInputDialog(self):
        """
        Shows the 'Zoom to what3words address' dock widget.
        """
        self.warningAPIsettings()
        
        if self.zoomToDialog.isHidden():
            self.zoomToDialog.show()
            self._showMessage("Start typing a what3words address, e.g. index.home.raft", Qgis.Info)
        else:
            self.zoomToDialog.hide()

    def toggleGrid(self, checked):
        """
        Toggles the What3words grid on and off and updates the button text.
        """
        self.warningAPIsettings()
        
        if self.gridManager is None:
            self.gridManager = W3WGridManager(self.iface.mapCanvas())

        if checked:
            self.gridManager.enableGrid(True)
            self.gridToggleAction.setText("Hide Grid")
            self._showMessage("what3words Grid enabled.", Qgis.Info)
        else:
            self.gridManager.enableGrid(False)
            self.gridToggleAction.setText("View Grid")
            self._showMessage("what3words Grid disabled.", Qgis.Info)

    def toggleTool(self):
        """
        Activates or deactivates the what3words map tool for converting map clicks to 3-word addresses.
        """
        self.warningAPIsettings()

        # Toggle the map tool on or off based on its current state
        if self.iface.mapCanvas().mapTool() == self.mapTool:
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            self.toolAction.setChecked(False)
        else:
            if not self.mapTool:
                self.mapTool = W3WMapTool(self.iface.mapCanvas())
            
            self.iface.mapCanvas().setMapTool(self.mapTool)
            self.toolAction.setChecked(True)
            self._showMessage("View what3words address tool activated. Click on the map to get what3words address.", Qgis.Info)

    def unsetTool(self, tool):
        """
        Unchecks the map tool action if another map tool is set.
        """
        if tool != self.mapTool:
            self.toolAction.setChecked(False)
            
    def unload(self):
        """
        Cleans up all components when the plugin is unloaded.
        """
        if self.gridManager and self.gridManager.grid_enabled:
            self.gridManager.enableGrid(False)

        self.iface.removeToolBarIcon(self.gridToggleAction)
        self.iface.removePluginMenu("what3words", self.gridToggleAction)
        
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
        if hasattr(self, 'toolAction'):
            self.iface.removeToolBarIcon(self.toolAction)
            self.iface.removePluginMenu("what3words", self.toolAction)
            del self.toolAction

        if hasattr(self, 'zoomToAction'):
            self.iface.removeToolBarIcon(self.zoomToAction)
            self.iface.removePluginMenu("what3words", self.zoomToAction)
            del self.zoomToAction
        
        self.iface.removeToolBarIcon(self.settingsAction)
        self.iface.removeDockWidget(self.zoomToDialog)

        removeSettingsMenu("what3words")
        removeHelpMenu("what3words")
        removeAboutMenu("what3words")
        unregister_w3w_functions()

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
        
