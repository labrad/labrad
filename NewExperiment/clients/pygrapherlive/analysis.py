'''
Analysis Widget
'''
from PyQt4 import QtCore, QtGui
from twisted.internet.defer import inlineCallbacks
import numpy as np
from scipy import optimize

from fitgaussian import FitGaussian
from fitline import FitLine
from fitlorentzian import FitLorentzian
from fitparabola import FitParabola

class AnalysisWidget(QtGui.QWidget):
    """Creates the window for the new plot"""
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)  
        self.parent = parent     
        self.cxn = self.parent.parent.cxn
        self.createContext()
        self.analysisCheckboxes = {}      

        self.fitLine = FitLine(self)
        self.fitGaussian = FitGaussian(self)
        self.fitLorentzian = FitLorentzian(self)
        self.fitParabola = FitParabola(self)
        self.fitCurveDictionary = {self.fitLine.curveName: self.fitLine,
                                   self.fitGaussian.curveName: self.fitGaussian,
                                   self.fitLorentzian.curveName: self.fitLorentzian,
                                   self.fitParabola.curveName: self.fitParabola
                                   }           

        self.parameterWindow = ParameterWindow(self)
        self.solutionsDictionary = {}
        self.setMaximumWidth(200)

        mainLayout = QtGui.QVBoxLayout()
                
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(5)
        
        title = QtGui.QLabel()
        title.setText('Analysis')
              
        dummyLayout = QtGui.QHBoxLayout()
        mainLayout.addLayout(dummyLayout)
        dummyLayout.addWidget(title, QtCore.Qt.AlignCenter)

        i = 0;
        for key in self.fitCurveDictionary.keys():
            self.analysisCheckboxes[key] = QtGui.QCheckBox(key, self)
            if (i % 2 == 0): #even
                self.grid.addWidget(self.analysisCheckboxes[key], (i / 2), 0, QtCore.Qt.AlignLeft)
            else:
                self.grid.addWidget(self.analysisCheckboxes[key], ((i - 1) / 2), 1, QtCore.Qt.AlignLeft)                
            i += 1

        mainLayout.addLayout(self.grid)
        
        # Layout for keeping track of datasets on a graph and analysis
        self.datasetCheckboxListWidget = QtGui.QListWidget()
        self.datasetCheckboxListWidget.setMaximumWidth(180)
        self.datasetCheckboxListWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mainLayout.addWidget(self.datasetCheckboxListWidget)

        # button to fit data on screen
        parametersButton = QtGui.QPushButton("Parameters", self)
        parametersButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        parametersButton.clicked.connect(self.setParameters)        
        mainLayout.addWidget(parametersButton)
        
        # button to fit data on screen
        fitButton = QtGui.QPushButton("Fit Curves", self)
        fitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        fitButton.clicked.connect(self.fitCurvesSignal)        
        mainLayout.addWidget(fitButton)
        
        # button to fit data on screen
        drawButton = QtGui.QPushButton("Draw Curves", self)
        drawButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        drawButton.clicked.connect(self.drawCurvesSignal)        
        mainLayout.addWidget(drawButton)        
        
        # button to fit data on screen
        togglePointsButton = QtGui.QPushButton("Toggle Points", self)
        togglePointsButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        togglePointsButton.clicked.connect(self.togglePointsSignal)        
        mainLayout.addWidget(togglePointsButton)        
        
        self.setLayout(mainLayout)        

    @inlineCallbacks
    def createContext(self):
        self.context = yield self.cxn.context()

    def setParameters(self, evt):
        self.parameterWindow.setRanges()
        self.parameterWindow.show()
        # create the parameter window upstairs, spinboxes will be part of it

    def togglePointsSignal(self, evt):
        for dataset,directory,index in self.parent.datasetAnalysisCheckboxes.keys():
            # if dataset is intended to be drawn (a checkbox governs this)
            if self.parent.datasetAnalysisCheckboxes[dataset, directory, index].isChecked():
                self.parent.qmc.togglePoints(dataset, directory, index)
            else:
                self.parent.qmc.toggleLine(dataset, directory, index)
            
                
                    
    def fitCurvesSignal(self, evt):
        self.fitCurves()
        
    def drawCurvesSignal(self, evt):
        self.fitCurves(drawCurves = True)

    def fitCurves(self, parameters = None, drawCurves = False):
        self.solutionsDictionary = {}
        for dataset,directory,index in self.parent.datasetAnalysisCheckboxes.keys():
            # if dataset is intended to be drawn (a checkbox governs this)
            if self.parent.datasetAnalysisCheckboxes[dataset, directory, index].isChecked():
                for key in self.analysisCheckboxes.keys():
                    if self.analysisCheckboxes[key].isChecked():
                        labels = self.parent.qmc.datasetLabelsDict[dataset, directory]
#                        print dataset, directory, index, key
                        # MULTIPLE LINES IN THE SAME DATASET!!!!
                        fitFunction = self.fitCurveDictionary[key].fitCurve
                        fitFunction(dataset, directory, index, labels[index], parameters, drawCurves)
        if (drawCurves == False):                        
            self.solutionsWindow = SolutionsWindow(self, self.context, self.solutionsDictionary)
            self.solutionsWindow.show()


class ParameterWindow(QtGui.QWidget):
    """Creates the fitting parameter window"""

    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.setWindowTitle('Analysis Parameters')
#        self.parameterLabels = [] # a list of lists maybe? [['Gaussian', 'Height', 'Sigma'...], ['Lorentzian', ...]..]
#        self.parameterDoubleSpinBoxes = [] 
        self.parameterWidgets = {} # a list of lists maybe? [['Gaussian', 'Height', heightspinbox, 'Sigma', sigmaspinbox...], ['Lorentzian', ...]..]
        self.setupUI()
    
    def setupUI(self):
        
                # Layout
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(5)
        
        # okay here we go:
        for key in self.parent.fitCurveDictionary.keys():
            j = 0
            self.parameterWidgets[key] = []
            for parameterName in self.parent.fitCurveDictionary[key].parameterNames:
                # Create things
                self.parameterWidgets[key].append(QtGui.QLabel(parameterName))
                self.parameterWidgets[key].append(QtGui.QDoubleSpinBox())
                self.parameterWidgets[key][j*2+1].setDecimals(6)
                self.parameterWidgets[key][j*2+1].setRange(-1000000000, 1000000000)
                self.parameterWidgets[key][j*2+1].setValue(1)
                self.parameterWidgets[key][j*2+1].setSingleStep(.1)
                self.parameterWidgets[key][j*2+1].setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
                self.parameterWidgets[key][j*2+1].setKeyboardTracking(False)
                self.connect(self.parameterWidgets[key][j*2+1], QtCore.SIGNAL('valueChanged(double)'), self.parent.drawCurvesSignal)
                j += 1
        
        i = 0             
        for key in self.parameterWidgets.keys():
            curveLabel = QtGui.QLabel(key)
            self.grid.addWidget(curveLabel, i, 0, QtCore.Qt.AlignCenter)
            for j in range(len(self.parameterWidgets[key])):
                self.grid.addWidget(self.parameterWidgets[key][j], i, j+1, QtCore.Qt.AlignCenter)
            i += 1

    def setRanges(self):
        xmin, xmax = self.parent.parent.qmc.getDataXLimits()
        fitRangeLabel = QtGui.QLabel('Fit Range: ')
        self.minRange = QtGui.QDoubleSpinBox()
        self.minRange.setDecimals(6)
        self.minRange.setRange(xmin, xmax)
        self.minRange.setValue(xmin)
        self.minRange.setSingleStep(.1)
        self.minRange.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.minRange.setKeyboardTracking(False)
        self.connect(self.minRange, QtCore.SIGNAL('valueChanged(double)'), self.minRangeSignal)
        self.maxRange = QtGui.QDoubleSpinBox()
        self.maxRange = QtGui.QDoubleSpinBox()
        self.maxRange.setDecimals(6)
        self.maxRange.setRange(xmin, xmax)
        self.maxRange.setValue(xmax)
        self.maxRange.setSingleStep(.1)
        self.maxRange.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.maxRange.setKeyboardTracking(False)  
        self.connect(self.maxRange, QtCore.SIGNAL('valueChanged(double)'), self.maxRangeSignal)
        
        i = len(self.parameterWidgets.keys())
        self.grid.addWidget(fitRangeLabel, i, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.minRange, i, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.maxRange, i, 2, QtCore.Qt.AlignCenter)             
         
        # Title Labels       
        # Maybe there's no need to show the whole function
#        gaussianLabel = QtGui.QLabel('Gaussian:  Height*exp(-(((x - center)/Sigma)**2)/2) + Offset')
#        lorentzianLabel = QtGui.QLabel('Lorentzian: Offset + I*(Gamma**2/((x - Center)**2 + Gamma**2))')
#        lineLabel = QtGui.QLabel('Line: Slope*x + Offset')
#        parabolaLabel = QtGui.QLabel('Parabola: A*x**2 + B*x + C ')

        self.setFixedSize(1000, 200)

    def minRangeSignal(self, evt):
        self.minRange.setRange(self.minRange.minimum(), self.maxRange.value())
    def maxRangeSignal(self, evt):
        self.maxRange.setRange(self.minRange.value(), self.maxRange.maximum())

    def closeEvent(self, evt):
        self.hide()        

class SolutionsWindow(QtGui.QWidget):
    """Creates the fitting parameter window"""

    def __init__(self, parent, context, solutionsDictionary):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.context = context
        self.solutionsDictionary = solutionsDictionary
        self.labels = []
        self.textBoxes = []
#        self.refitButtons = []
        self.acceptButtons = []
        self.setWindowTitle('Solutions')
        self.buttonIndexDict = {}
#        self.refitButtonIndexDict = {}
        self.setupUI()
   
    def setupUI(self):
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(5)        
        
        for dataset, directory, label, curve, parameters, index in self.solutionsDictionary.keys():
            datasetLabel = QtGui.QLabel(str(dataset) + ' - ' + str(directory[-1]) + ' - ' + label)
            self.labels.append(datasetLabel)
            textBox = QtGui.QLineEdit(readOnly=True)
            textBox.setText('\'Fit\', [\'['+str(index)+']\', \''+ str(curve) + '\', ' + '\'' + str(self.solutionsDictionary[dataset, directory, label, curve, parameters, index]) + '\']')
            textBox.setMinimumWidth(550)
            self.textBoxes.append(textBox)
#            refitButton = QtGui.QPushButton("Refit Curve", self)
#            refitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
#            refitButton.clicked.connect(self.refitSignal)    
#            self.refitButtons.append(refitButton)
#            self.refitButtonIndexDict[refitButton] = [dataset, directory, index, curve, str(self.solutionsDictionary[dataset, directory, label, curve, parameters, index])]        
            acceptButton = QtGui.QPushButton("Accept", self)
            acceptButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
            acceptButton.clicked.connect(self.acceptSignal)  
            self.acceptButtons.append(acceptButton)          
            self.buttonIndexDict[acceptButton] = [dataset, directory, label, curve, parameters, index]
        
        for i in range(len(self.labels)):
            self.grid.addWidget(self.labels[i], i, 0, QtCore.Qt.AlignCenter)
            self.grid.addWidget(self.textBoxes[i], i, 1, QtCore.Qt.AlignCenter)
#            self.grid.addWidget(self.refitButtons[i], i, 2, QtCore.Qt.AlignCenter)
            self.grid.addWidget(self.acceptButtons[i], i, 2, QtCore.Qt.AlignCenter)

        self.setLayout(self.grid)
        self.show()
    
    @inlineCallbacks
    def acceptSignal(self, evt):
        readyToClose = True
        button = self.sender()
        dataset, directory, label, curve, parameters, index = self.buttonIndexDict[button]
        yield self.parent.cxn.data_vault.cd(directory, context = self.context)
        yield self.parent.cxn.data_vault.open(dataset, context = self.context)
        yield self.parent.cxn.data_vault.add_parameter_over_write('Accept-' + str(index), True, context = self.context)

        # now you gotta set solutions to parameters!     
        # kinda ugly, let's debug first
        # somehow you gotta get access to curveName and solutions from here!
        i = 0
        j = 0
        for parameter in self.parent.parameterWindow.parameterWidgets[curve]:
            if (i % 2 == 0): #even
                pass
            else:
                self.parent.parameterWindow.parameterWidgets[curve][i].blockSignals(True)
                self.parent.parameterWindow.parameterWidgets[curve][i].setValue(self.solutionsDictionary[dataset, directory, label, curve, parameters, index][j])
                self.parent.parameterWindow.parameterWidgets[curve][i].blockSignals(False)
                j += 1
            i += 1
        
        # cycle through accept buttons, if it's the sender, gray it out
        # if any of the other accept buttons are still active, stop the loop!
        for i in range(len(self.acceptButtons)):
            if (button == self.acceptButtons[i]):
                button.setEnabled(False)
            else:
                if self.acceptButtons[i].isEnabled():
                    readyToClose = False
        if (readyToClose):
            self.close()   
        
#    def refitSignal(self, evt):
#        dataset, directory, index, curve, parameters = self.refitButtonIndexDict[self.sender()]
#        scriptParameters = [str('['+str(index+1)+']'), str(curve), parameters]
#        print scriptParameters
#        self.parent.parent.fitFromScript(dataset, directory, 1, scriptParameters, True)