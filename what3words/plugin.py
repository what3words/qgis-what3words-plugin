from __future__ import absolute_import

import os
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
from what3words.w3wfunctions import register_w3w_functions, unregister_w3w_functions 
from what3words.processingprovider.w3wprovider import W3WProvider


class W3WTools(object):

    def __init__(self, iface):
        self.iface = iface
        self.coordDialog = None 
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
        self.coordDialog = W3WCoordInputDialog(self.iface.mapCanvas(), self.iface.mainWindow())
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.coordDialog)
        self.coordDialog.settingsButtonClicked.connect(self.toggleSettingsAction)  # Connect signal
        self.coordDialog.hide()

        # Add zoom to what3words address button
        if not hasattr(self, 'coordDialogAction'):
            coordDialogIcon = QIcon(os.path.join(os.path.dirname(__file__), "icons", "w3w.svg"))
            self.coordDialogAction = QAction(coordDialogIcon, "Discover what3words address", self.iface.mainWindow())
            self.coordDialogAction.triggered.connect(self.showW3WCoordInputDialog)
            self.coordDialogAction.setCheckable(True)
            self.coordDialog.coordDialogAction = self.coordDialogAction  # Pass the action to the dock widget
            self.iface.addToolBarIcon(self.coordDialogAction)
            self.iface.addPluginToMenu("what3words", self.coordDialogAction)
        
        # Add settings button to toolbar
        if not hasattr(self, 'settingsAction'):
            self.settingsAction = QAction(QgsApplication.getThemeIcon('/mActionOptions.svg'), "Settings",iface.mainWindow())
            self.settingsAction.setCheckable(True)
            self.settingsAction.triggered.connect(self.showSettingsDialog)
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
        if hasattr(self, 'settingsDialog') and self.settingsDialog is not None:
            self.settingsDialog.raise_()
            return

        self.settingsAction.setEnabled(False)
        self.coordDialog.settingsButton.setEnabled(False)  # Disable coordDialog button

        self.settingsDialog = ConfigDialog("what3words")
        self.settingsDialog.finished.connect(self.onSettingsDialogClosed)
        self.settingsDialog.show()

    def onSettingsDialogClosed(self):
        """
        Callback when the settings dialog is closed. Re-enables the settings button.
        """
        self.settingsAction.setEnabled(True)
        self.coordDialog.settingsButton.setEnabled(True)  # Re-enable coordDialog button
        self.settingsDialog = None  # Reset dialog reference

    def toggleSettingsAction(self, disable):
        """
        Enables or disables the main menu settings button based on coordDialog's state.
        """
        self.settingsAction.setEnabled(not disable)

    def showW3WCoordInputDialog(self):
        """
        Shows the 'Zoom to what3words address' dock widget.
        Ensures the associated button remains consistent with the visibility state.
        """

        if not self.coordDialog.isVisible():
            self.coordDialog.show()
            self.coordDialogAction.setChecked(True)  # Ensure the button is checked
        else:
            self.coordDialog.hide()
            self.coordDialogAction.setChecked(False)  # Ensure the button is unchecked

    def unload(self):
        """
        Cleans up all components when the plugin is unloaded.
        """
        # Remove coorddialog action if present
        if hasattr(self, 'coordDialogAction'):
            self.iface.removeToolBarIcon(self.coordDialogAction)
            self.iface.removePluginMenu("what3words", self.coordDialogAction)
            del self.coordDialogAction

        # Remove settings action if present
        if hasattr(self, 'settingsAction'):
            self.iface.removeToolBarIcon(self.settingsAction)
            self.iface.removePluginMenu("what3words", self.settingsAction)
            del self.settingsAction

        # Remove the dock widget
        if self.coordDialog:
            self.iface.removeDockWidget(self.coordDialog)

        if "what3words" in _settingActions:
            removeSettingsMenu("what3words")

        # Safely remove help menu if it exists
        try:
            removeHelpMenu("what3words")
        except KeyError:
            iface.messageBar().pushMessage(
                "what3words", "Help menu was not found during unload.", level=Qgis.Warning)

        # Safely remove about menu if it exists
        try:
            removeAboutMenu("what3words")
        except KeyError:
            iface.messageBar().pushMessage(
                "what3words", "About menu was not found during unload.", level=Qgis.Warning)

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
        
