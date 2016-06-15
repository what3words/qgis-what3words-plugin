# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from PyQt4 import QtGui, QtCore
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from w3w import what3words
from apikey import apikey

class W3WCoordInputDialog(QtGui.QDockWidget):
    def __init__(self, canvas, parent):
        self.canvas = canvas
        self.marker = None
        QtGui.QDockWidget.__init__(self, parent)
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea)
        self.initGui()

    def setApiKey(self, apikey):
        self.w3w = what3words(apikey=apikey)

    def initGui(self):
        self.setWindowTitle("Zoom to 3 word address")
        self.label = QtGui.QLabel('3 Word Address')
        self.coordBox = QtGui.QLineEdit()
        self.coordBox.returnPressed.connect(self.zoomToPressed)
        self.zoomToButton = QtGui.QPushButton("Zoom to")
        self.zoomToButton.clicked.connect(self.zoomToPressed)
        self.removeMarkerButton = QtGui.QPushButton("Remove marker")
        self.removeMarkerButton.clicked.connect(self.removeMarker)
        self.removeMarkerButton.setDisabled(True)
        self.hlayout = QtGui.QHBoxLayout()
        self.hlayout.setSpacing(6)
        self.hlayout.setMargin(9)
        self.hlayout.addWidget(self.label)
        self.hlayout.addWidget(self.coordBox)
        self.hlayout.addWidget(self.zoomToButton)
        self.hlayout.addWidget(self.removeMarkerButton)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setLayout(self.hlayout)
        self.setWidget(self.dockWidgetContents)

    def zoomToPressed(self):
        try:
            w3wCoord = str(self.coordBox.text()).replace(" ", "")
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            json = self.w3w.forwardGeocode(w3wCoord)
            lat = float(json["geometry"]["lat"])
            lon = float(json["geometry"]["lng"])
            canvasCrs = self.canvas.mapSettings().destinationCrs()
            epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
            transform4326 = QgsCoordinateTransform(epsg4326, canvasCrs)
            center = transform4326.transform(lon, lat)
            self.canvas.zoomByFactor(1, center)
            self.canvas.refresh()
            if self.marker is None:
                self.marker = QgsVertexMarker(self.canvas)
            self.marker.setCenter(center)
            self.marker.setIconSize(8)
            self.marker.setPenWidth(4)
            self.removeMarkerButton.setDisabled(False)
            self.coordBox.setStyleSheet("QLineEdit{background: white}")
        except Exception, e:
            self.coordBox.setStyleSheet("QLineEdit{background: yellow}")
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def removeMarker(self):
        self.canvas.scene().removeItem(self.marker)
        self.marker = None

    def closeEvent(self, evt):
        if self.marker is not None:
            self.canvas.scene().removeItem(self.marker)
            self.marker = None
