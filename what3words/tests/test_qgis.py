import sys
import os

# Set QGIS paths
os.environ['PYTHONPATH'] = '/Applications/QGIS-LTR.app/Contents/Resources/python'
sys.path.append('/Applications/QGIS-LTR.app/Contents/Resources/python')
sys.path.append('/Applications/QGIS-LTR.app/Contents/Resources/python/plugins')

# Import QGIS modules
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QApplication
from qgis.analysis import QgsNativeAlgorithms

# Initialize QGIS application
QgsApplication.setPrefixPath('/Applications/QGIS-LTR.app/Contents/MacOS', True)
qgs_app = QgsApplication([], False)
qgs_app.initQgis()
