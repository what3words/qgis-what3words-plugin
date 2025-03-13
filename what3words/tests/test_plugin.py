import unittest
from unittest.mock import MagicMock, patch
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction
from what3words.plugin import W3WTools
from what3words.coorddialog_new_ui import W3WCoordInputDialog
from what3words.processingprovider.w3wprovider import W3WProvider
from qgis.PyQt.QtWidgets import QMainWindow
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QApplication
import sys
import os
# Set QGIS paths
os.environ['PYTHONPATH'] = '/Applications/QGIS-LTR.app/Contents/Resources/python'
os.environ['PROJ_LIB'] = '/Applications/QGIS-LTR.app/Contents/Resources/proj'
sys.path.append('/Applications/QGIS-LTR.app/Contents/Resources/python')
sys.path.append('/Applications/QGIS-LTR.app/Contents/Resources/python/plugins')
sys.path.append('/Applications/QGIS-LTR.app/Contents/Resources/python/plugins/processing')
sys.path.append('/Users/manuelasabatino/Documents/w3w_workspace/w3w_qgis/qgis-what3words-plugin')


class TestW3WTools(unittest.TestCase):
    def setUp(self):
        # Mock iface
        self.iface = MagicMock()
        self.iface.mainWindow.return_value = QMainWindow()
        self.iface.removePluginMenu = MagicMock()
        self.iface.addDockWidget = MagicMock()
        self.iface.addToolBarIcon = MagicMock()
        self.iface.addPluginToMenu = MagicMock()

        # Initialize plugin
        self.plugin = W3WTools(self.iface)

    @patch('what3words.plugin.W3WCoordInputDialog')
    def test_initGui(self, MockW3WCoordInputDialog):
        self.plugin.initGui()

        # Ensure coordDialog is initialized and added to the dock
        MockW3WCoordInputDialog.assert_called_once_with(self.iface.mapCanvas(), self.iface.mainWindow())
        self.iface.addDockWidget.assert_called_once_with(Qt.TopDockWidgetArea, self.plugin.coordDialog)

        # Check QAction creation
        self.assertTrue(hasattr(self.plugin, 'coordDialogAction'))
        self.assertIsInstance(self.plugin.coordDialogAction, QAction)
        self.assertEqual(self.plugin.coordDialogAction.text(), "Discover what3words address")
        self.iface.addToolBarIcon.assert_called_with(self.plugin.coordDialogAction)

    @patch('what3words.plugin.ConfigDialog')
    def test_showSettingsDialog(self, MockConfigDialog):
        self.plugin.initGui()  # Ensure GUI is initialized
        self.plugin.showSettingsDialog()

        # Ensure settings dialog is shown
        mock_dialog = MockConfigDialog.return_value
        self.assertIsNotNone(self.plugin.settingsDialog)
        mock_dialog.show.assert_called_once()

    @patch('what3words.plugin.removeHelpMenu')
    def test_unload(self, mock_removeHelpMenu):
        self.plugin.unload()

        # Verify help menu removal
        mock_removeHelpMenu.assert_called_once_with("what3words")
        self.iface.removeToolBarIcon.assert_any_call(self.plugin.coordDialogAction)
        self.iface.removePluginMenu.assert_any_call("what3words", self.plugin.coordDialogAction)

if __name__ == '__main__':
    unittest.main()