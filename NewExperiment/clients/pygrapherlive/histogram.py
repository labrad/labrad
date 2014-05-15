import sys
from PyQt4 import QtGui, QtCore
from matplotlib.figure import Figure
from matplotlib import cm
import matplotlib.pyplot as plt
import time


from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread
from datetime import datetime

import matplotlib.pyplot as plt


import numpy as np

class HistCanvas(FigureCanvas):
    """Matplotlib Figure widget to display CPU utilization"""
    def __init__(self, parent, data, threshold):
        self.parent = parent
        self.data = data
        self.threshold = threshold
        self.fig = Figure()
        FigureCanvas.__init__(self, self.fig)

        self.ax = self.fig.add_subplot(111)

        self.ax.bar(data[:,0], data[:,1], width = np.max(data[:,0])/len(data[:,0]), label = 'Data')
#        ymin, ymax = self.ax.get_ylim()
#        thresholdY = np.arange(ymin, ymax)
#        thresholdX = [self.threshold]*len(thresholdY)
#        self.ax.plot(thresholdX, thresholdY, color = 'r', linewidth=2.0, label = 'Threshold')
        self.thresholdLine = self.ax.axvline(self.threshold, ymin=0, ymax= 200, linewidth=3.0, color = 'r', label = 'Threshold')
        self.ax.legend(loc='best')
        #self.ax.set_ylim(0, 1)
    
    def updateHistogram(self, binsValue):
        self.ax.cla()
        self.ax.hist(self.data, bins = binsValue, align='left', label = 'test')
        self.ax.legend(loc='best')      
               
    def thresholdChange(self, threshold):
        self.thresholdLine.remove()
        self.thresholdLine = self.ax.axvline(threshold, ymin=0, ymax= 200, linewidth=3.0, color = 'r', label = 'Threshold')
        self.draw()
        
class HistWindow(QtGui.QWidget):        
    """Creates the window for the new plot"""
    def __init__(self, parent, data, threshold, title):
        QtGui.QWidget.__init__(self)
        
        self.parent = parent
        self.threshold = threshold
        self.setWindowTitle(title)
        
        layout = QtGui.QVBoxLayout()


#        self.binSpinBox = QtGui.QSpinBox()
#        self.binSpinBox.setMinimum(0)
#        self.binSpinBox.setMaximum(500)
#        self.binSpinBox.setSingleStep(1)  
#        self.binSpinBox.setValue(30)     
#        self.binSpinBox.setKeyboardTracking(False)
#        self.connect(self.binSpinBox, QtCore.SIGNAL('valueChanged(int)'), self.binChange)
        
        self.thresholdSpinBox = QtGui.QSpinBox()
        self.thresholdSpinBox.setMinimum(-100)
        self.thresholdSpinBox.setMaximum(100000)
        self.thresholdSpinBox.setSingleStep(1)  
        self.thresholdSpinBox.setValue(self.threshold)     
        self.thresholdSpinBox.setKeyboardTracking(False)
        self.connect(self.thresholdSpinBox, QtCore.SIGNAL('valueChanged(int)'), self.thresholdChange)  
        
        #try:
        self.canvas = HistCanvas(self, data, self.thresholdSpinBox.value())
        #except AttributeError:
            #raise Exception("Has a Dark Ion Catalog Been Retrieved?")
        self.canvas.show()
        ntb = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.canvas)
        layout.addWidget(ntb)
        
#        changeWindowTitleButton = QtGui.QPushButton("Change Window Title", self)
#        changeWindowTitleButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
#        changeWindowTitleButton.clicked.connect(self.changeWindowTitle)
        
              
        
        self.bottomPanel = QtGui.QHBoxLayout()
        
        layout.addLayout(self.bottomPanel)
#        self.bottomPanel.addWidget(self.binSpinBox)
        self.bottomPanel.addWidget(self.thresholdSpinBox)
        
        
        self.setLayout(layout)
        #self.show()
    
    
    def binChange(self, evt):
        self.canvas.updateHistogram(self.binSpinBox.value())
        
    def thresholdChange(self, evt):
        self.canvas.thresholdChange(self.thresholdSpinBox.value())        

#class Histogrammer(QtGui.QWidget):        
#    """Creates the window for the new plot"""
#    def __init__(self, parent):
#        QtGui.QWidget.__init__(self)
#        
#        self.parent = parent
#        self.histList = []
#
#
#    @inlineCallbacks
#    def newHistogram(self, dataset, directory):
#        yield self.server.cd(directory)
#        yield self.server.open(dataset)
#        Data = yield self.server.get()
#        data = Data.asarray
#        
#        histWindow = HistWindow(self, data)
#        self.histList.append(histWindow)
#        histWindow.show()        
