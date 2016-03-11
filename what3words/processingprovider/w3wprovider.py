import os
from processing.core.AlgorithmProvider import AlgorithmProvider
from add3wordsfield import Add3WordsFieldAlgorithm
from PyQt4.QtGui import QIcon

class W3WProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = True

        # Load algorithms
        self.alglist = [Add3WordsFieldAlgorithm()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)


    def unload(self):
        AlgorithmProvider.unload(self)


    def getName(self):
        return 'what3words'

    def getDescription(self):
        return 'what3words tools'

    def getIcon(self):
        return QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), "w3w.png"))
        
    def _loadAlgorithms(self):
        self.algs = self.alglist
