from __future__ import absolute_import

import os
import webbrowser
from builtins import object

from qgis.core import Qgis, QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface
from qgiscommons2.gui import (addAboutMenu, addHelpMenu, removeAboutMenu,
                              removeHelpMenu)
from qgiscommons2.gui.settings import removeSettingsMenu, _settingActions, ConfigDialog
from qgiscommons2.settings import pluginSetting, readSettings

from what3words.coorddialog_new_ui import W3WCoordInputDialog 
from what3words.maptool import W3WMapTool
from what3words.grid import W3WGridManager
from what3words.w3wfunctions import register_w3w_functions, unregister_w3w_functions 
from what3words.processingprovider.w3wprovider import W3WProvider


class W3WTools(object):

    def __init__(self, iface):
        self.iface = iface
        self.gridManager = None  
        self.mapTool = None
        self.zoomToDialog = None 
        self.settingsDialog = None
        self.provider = W3WProvider()
        register_w3w_functions() 
        
        try:
            from qgistester.tests import addTestModule
            from what3words.tests import testerplugin
            addTestModule(testerplugin, "what3words")
        except:
            pass

        readSettings()

    def initGui(self):
        # Add the dock widget for zooming to w3w
        self.zoomToDialog = W3WCoordInputDialog(self.iface.mapCanvas(), self.iface.mainWindow())
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()

        # Add zoom to what3words address button
        if not hasattr(self, 'zoomToAction'):
            zoomToIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w.svg"))
            self.zoomToAction = QAction(zoomToIcon, "Discover what3words address", self.iface.mainWindow())
            self.zoomToAction.triggered.connect(self.showW3WCoordInputDialog)
            self.zoomToAction.setCheckable(True)
            self.zoomToDialog.zoomToAction = self.zoomToAction  # Pass the action to the dock widget
            self.iface.addToolBarIcon(self.zoomToAction)
            self.iface.addPluginToMenu("what3words", self.zoomToAction)
        
        # Add map tool button
        if not hasattr(self, 'toolAction'):
            mapToolIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w_marker.svg"))
            self.toolAction = QAction(mapToolIcon, "View what3words address", self.iface.mainWindow())
            self.toolAction.triggered.connect(self.zoomToDialog.toggleCaptureTool)
            self.toolAction.setCheckable(True)
            # self.iface.addToolBarIcon(self.toolAction)
            # self.iface.addPluginToMenu("what3words", self.toolAction)


        # Add grid toggle button with dynamic text updates
        if not hasattr(self, 'gridToggleAction'):
            gridIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "grid_red.svg"))
            self.gridToggleAction = QAction(gridIcon, "View Grid", self.iface.mainWindow())
            self.gridToggleAction.setCheckable(True)
            self.gridToggleAction.toggled.connect(self.zoomToDialog.toggleGrid)
            # self.iface.addToolBarIcon(self.gridToggleAction)
            # self.iface.addPluginToMenu("what3words", self.gridToggleAction)

         # Add open mapsite button
        if not hasattr(self, 'openMapsiteAction'):
            mapsiteIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w_search.svg"))
            self.openMapsiteAction = QAction(mapsiteIcon, "Open Mapsite", self.iface.mainWindow())
            self.openMapsiteAction.triggered.connect(self.zoomToDialog.toggleMapToolForMapsite)
            self.openMapsiteAction.setCheckable(True)
            # self.iface.addToolBarIcon(self.openMapsiteAction)
            # self.iface.addPluginToMenu("what3words", self.openMapsiteAction)

        # Add settings button to toolbar
        if not hasattr(self, 'settingsAction'):
            self.settingsAction = QAction(QgsApplication.getThemeIcon('/mActionOptions.svg'), "Settings",iface.mainWindow())
            self.settingsAction.setCheckable(True)
            self.settingsAction.triggered.connect(self.showSettingsDialog)
            # self.iface.addToolBarIcon(self.settingsAction)
            self.iface.addPluginToMenu("what3words", self.settingsAction)

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
        Opens the settings dialog if it's not already open. Disables the settings button
        while the dialog is open and re-enables it when the dialog is closed.
        """
        # Check if the dialog is already open
        if self.settingsDialog is not None:
            # Bring the dialog to the front if it's already open
            self.settingsDialog.raise_()
            return

        # Attempt to open the settings dialog
        self.settingsDialog = ConfigDialog("what3words")

        # If openSettingsDialog did not return a valid dialog, handle it with a message
        if self.settingsDialog is None:
            self._showMessage("Error: Could not open settings dialog.", Qgis.Critical)
            return

        self.settingsAction.setEnabled(False)
        self.settingsDialog.finished.connect(self.onSettingsDialogClosed)
        self.settingsDialog.show()

    def onSettingsDialogClosed(self):
        """
        Callback when the settings dialog is closed. Re-enables the settings button.
        """
        self.settingsAction.setEnabled(True)
        self.settingsDialog = None  # Reset dialog reference

    def warningAPIsettings(self):
        apikey = pluginSetting("apiKey", namespace="what3words")
        if not apikey:
            self._showMessage('what3words API key is not set. Please set it and try again.', Qgis.Warning)
            return

    def showW3WCoordInputDialog(self):
        """
        Shows the 'Zoom to what3words address' dock widget.
        Ensures the associated button remains consistent with the visibility state.
        """
        self.warningAPIsettings()

        if not self.zoomToDialog.isVisible():
            self.zoomToDialog.show()
            self.zoomToAction.setChecked(True)  # Ensure the button is checked
        else:
            self.zoomToDialog.hide()
            self.zoomToAction.setChecked(False)  # Ensure the button is unchecked

    def unload(self):
        """
        Cleans up all components when the plugin is unloaded.
        """
        if self.gridManager and self.gridManager.grid_enabled:
            self.gridManager.enableGrid(False)

        # Remove the grid toggle action
        if hasattr(self, 'gridToggleAction'):
            self.iface.removeToolBarIcon(self.gridToggleAction)
            self.iface.removePluginMenu("what3words", self.gridToggleAction)
            del self.gridToggleAction

        # Unset map tool and remove tool action if present
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
        if hasattr(self, 'toolAction'):
            self.iface.removeToolBarIcon(self.toolAction)
            self.iface.removePluginMenu("what3words", self.toolAction)
            del self.toolAction

        # Remove zoom action if present
        if hasattr(self, 'zoomToAction'):
            self.iface.removeToolBarIcon(self.zoomToAction)
            self.iface.removePluginMenu("what3words", self.zoomToAction)
            del self.zoomToAction
        
        # Remove Open Mapsite action
        if hasattr(self, 'openMapsiteAction'):
            self.iface.removeToolBarIcon(self.openMapsiteAction)
            self.iface.removePluginMenu("what3words", self.openMapsiteAction)
            del self.openMapsiteAction

        # Remove settings action if present
        if hasattr(self, 'settingsAction'):
            self.iface.removeToolBarIcon(self.settingsAction)
            self.iface.removePluginMenu("what3words", self.settingsAction)
            del self.settingsAction

        # Remove the dock widget
        if self.zoomToDialog:
            self.iface.removeDockWidget(self.zoomToDialog)

        if "what3words" in _settingActions:
            removeSettingsMenu("what3words")

        # Remove help and about menus
        removeHelpMenu("what3words")
        removeAboutMenu("what3words")

        # Unregister functions and processing provider
        unregister_w3w_functions()
        QgsApplication.processingRegistry().removeProvider(self.provider)

        # Attempt to remove test modules and lessons folders if they exist
        try:
            from qgistester.tests import removeTestModule
            from what3words.tests import testerplugin
            removeTestModule(testerplugin, "what3words")
        except ImportError:
            pass

        try:
            from lessons import removeLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), '_lessons')
            removeLessonsFolder(folder)
        except ImportError:
            pass

    def _showMessage(self, message, level=Qgis.Info):
        iface.messageBar().pushMessage(
            message, level, iface.messageTimeout())
        
