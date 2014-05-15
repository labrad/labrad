'''
Analysis Window
'''
from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks
import numpy as np
from matplotlib import pylab

import getfrabiwindow

from fitgaussian import FitGaussian
from fitline import FitLine
from fitlorentzian import FitLorentzian
from fitparabola import FitParabola
from fitcosine import FitCosine
from fitramseyfringe import FitRamseyFringe
from fitrabiflop import FitRabiflop

class AnalysisWindow(QtGui.QWidget):
    
    def __init__(self, parent, ident):
        super(AnalysisWindow, self).__init__()
        self.dataset, self.directory, self.index = ident
        self.parent = parent     
        self.cxn = self.parent.parent.parent.cxn
        self.createContext()
        self.parameterSpinBoxes = {}
        self.parameterLabels = {} 
        self.solutionsDictionary = {}
        self.parameterSpinBoxDict = {}
        self.curveComboIndexDict = {}

        self.fitLine = FitLine(self)
        self.fitGaussian = FitGaussian(self)
        self.fitLorentzian = FitLorentzian(self,ident)
        self.fitParabola = FitParabola(self)
        self.fitCosine = FitCosine(self)
        self.fitRamseyFringe = FitRamseyFringe(self)
        self.fitRabiflop = FitRabiflop(self)
        self.fitCurveDictionary = {
                                   self.fitLorentzian.curveName: self.fitLorentzian,
                                   self.fitGaussian.curveName: self.fitGaussian,
                                   self.fitRamseyFringe.curveName: self.fitRamseyFringe,
                                   self.fitLine.curveName: self.fitLine,
                                   self.fitParabola.curveName: self.fitParabola,
                                   self.fitCosine.curveName: self.fitCosine,
                                   self.fitRabiflop.curveName: self.fitRabiflop                    
                                  }
        self.initUI()
        
    def initUI(self):      

        self.setWindowTitle('Fitting of '+str(self.directory))

        self.combo = QtGui.QComboBox(self)
        i = 0
        for curveName in self.fitCurveDictionary.keys():
            self.curveComboIndexDict[curveName] = i
            self.combo.addItem(curveName)
            self.combo.itemText(1)
            i += 1

#        self.lbl = QtGui.QLabel(self.combo.itemText(0), self)
#        self.hello1 = QtGui.QLabel('hi1', self)
#        self.hello2 = QtGui.QLabel('hi2', self)
#        self.hello3 = QtGui.QLabel('hi3', self)

        self.combo.move(50, 50)
#        self.lbl.move(50, 150)
        self.combo.activated[str].connect(self.onActivated)
            
#        self.setGeometry(300, 300, 500, 300)
        
        self.parameterTable = QtGui.QTableWidget()
        self.parameterTable.setColumnCount(4)
#        self.parameterTable.setHorizontalHeaderLabels(QtCore.QStringList(['Parameters','Manual','Fitted']))
#        self.parameterTable.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem('Parameters'))
#        self.horizontalHeader.setStretchLastSection(True)
        self.parameterTable.verticalHeader().setVisible(False)
        self.FitParameterBox={}
        self.FitParameterBoxChecked={}

        self.mainLayout = QtGui.QVBoxLayout()
        self.parameterLayout = QtGui.QHBoxLayout()
        self.buttonLayout = QtGui.QHBoxLayout()
        self.pitimesLayout = QtGui.QHBoxLayout()
       
        self.setLayout(self.mainLayout)
        self.mainLayout.addLayout(self.parameterLayout)
        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addLayout(self.pitimesLayout)
        
        self.parameterLayout.addWidget(self.combo)
        self.parameterLayout.addWidget(self.parameterTable)
#        self.grid.addWidget(self.combo, 0, 0, QtCore.Qt.AlignCenter)
        
        self.fitButton = QtGui.QPushButton("Fit", self)
        self.fitButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.fitButton.clicked.connect(self.fitCurveSignal)        

        self.acceptManualButton = QtGui.QPushButton("Accept Manual", self)
        self.acceptManualButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.acceptManualButton.clicked.connect(self.acceptManualSignal) 
        
        self.acceptFittedButton = QtGui.QPushButton("Accept Fitted", self)
        self.acceptFittedButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.acceptFittedButton.clicked.connect(self.acceptFittedSignal)   

        self.setRanges()
        fitRangeLabel = QtGui.QLabel('Fit Range: ')
        self.buttonLayout.addWidget(fitRangeLabel)
        self.buttonLayout.addWidget(self.minRange)
        self.buttonLayout.addWidget(self.maxRange)

        self.buttonLayout.addWidget(self.fitButton)
        self.buttonLayout.addWidget(self.acceptManualButton)
        self.buttonLayout.addWidget(self.acceptFittedButton)
        
        self.setPiTimes()
        self.TwoPiLabel = QtGui.QLabel('2Pi Time: (us)')
        self.PiLabel = QtGui.QLabel('Pi Time: (us)')
        self.PiOverTwoLabel = QtGui.QLabel('Pi/2 Time: (us)')
        self.pitimesLayout.addWidget(self.TwoPiLabel)
        self.pitimesLayout.addWidget(self.TwoPiTimeBox)
        self.pitimesLayout.addWidget(self.PiLabel)
        self.pitimesLayout.addWidget(self.PiTimeBox)
        self.pitimesLayout.addWidget(self.PiOverTwoLabel)
        self.pitimesLayout.addWidget(self.PiOverTwoTimeBox)
        
        self.manualTextLayout = QtGui.QHBoxLayout()
        manualLabel = QtGui.QLabel("Manual values: ")
        self.manualTextBox = QtGui.QLineEdit(readOnly=True)
        self.manualTextLayout.addWidget(manualLabel)
        self.manualTextLayout.addWidget(self.manualTextBox)
        #self.mainLayout.addLayout(self.manualTextLayout)     ##TEMPORARILY COMMENTED OUT FOR CLARITY, WE RARELY USED THESE TEXT PANELS

        self.fittedTextLayout = QtGui.QHBoxLayout()
        fittedLabel = QtGui.QLabel("Fitted values: ")
        self.fittedTextBox = QtGui.QLineEdit(readOnly=True)
        self.fittedTextLayout.addWidget(fittedLabel)
        self.fittedTextLayout.addWidget(self.fittedTextBox)
        #self.mainLayout.addLayout(self.fittedTextLayout)     ##TEMPORARILY COMMENTED OUT FOR CLARITY, WE RARELY USED THESE TEXT PANELS 

        #that additional 'guess f_Rabi button'
        self.guessfrabiButton = QtGui.QPushButton("Estimate f_Rabi", self)
        self.guessfrabiButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        self.guessfrabiButton.clicked.connect(self.guessfrabiClicked) 
        self.pitimesLayout.addWidget(self.guessfrabiButton)
        
        self.combo.setCurrentIndex(self.combo.findText('Lorentzian'))
        
        self.onActivated() #update parameterTable
        self.getDataParameter() #get Parameters from dataVault for initial values
        self.show()
    
    @inlineCallbacks
    def getDataParameter(self):
#        from labrad import units as U    
        try:
            yield self.parent.parent.parent.cxn.data_vault.cd(self.directory, context = self.context)
            yield self.parent.parent.parent.cxn.data_vault.open(1, context = self.context)
            sideband_selection = self.parent.parent.parent.cxn.data_vault.get_parameter('RabiFlopping.sideband_selection', context = self.context)
            sideband_selection = yield sideband_selection
            # START MOVE THIS PART TO WHERE IT CALLS THE (NOT YET IMPLEMENTED) PARAMETER 'experiment_name' to make it select the right initial fit function
            self.combo.setCurrentIndex(self.combo.findText('Rabi Flop'))
            self.onActivated()
            # END MOVE THIS
            sb = np.array(sideband_selection)
            if len(sb[sb.nonzero()])==1: #ONLY ONE SINGLE SIDEBAND SELECTED
                sideband=sb[sb.nonzero()][0]
                trap_frequencies = ['TrapFrequencies.radial_frequency_1','TrapFrequencies.radial_frequency_2','TrapFrequencies.axial_frequency','TrapFrequencies.rf_drive_frequency']
                trap_frequency = yield self.parent.parent.parent.cxn.data_vault.get_parameter(str(np.array(trap_frequencies)[sb.nonzero()][0]), context = self.context)
            elif len(sb[sb.nonzero()])==0: #NO SIDEBAND SELECTED -> CARRIER
                sideband=0
                print 'Warning: Carrier Rabi Flops will be represented in a 1D model using the first radial trap frequency as initial fit parameter!'
                trap_frequency = yield self.parent.parent.parent.cxn.data_vault.get_parameter('TrapFrequencies.radial_frequency_1', context = self.context)
            else: print 'Higher order sidebands not supported'
            #Set initial parameters
            self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, 'Rabi Flop'][0]['Sideband']=sideband
            self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, 'Rabi Flop'][0]['Trap Frequency']=trap_frequency['MHz']
            self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, 'Rabi Flop'][1]['Sideband']=sideband
            self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, 'Rabi Flop'][1]['Trap Frequency']=trap_frequency['MHz']
            self.onActivated()
        except:
            print 'No Rabi Flop data found'
        
    def setPiTimes(self):
        xmin, xmax = self.parent.parent.qmc.getDataXLimits()
        self.TwoPiTimeBox = QtGui.QDoubleSpinBox()
        self.TwoPiTimeBox.setDecimals(6)
        self.TwoPiTimeBox.setRange(xmin,2.0*xmax)
        self.connect(self.TwoPiTimeBox, QtCore.SIGNAL('editingFinished()'), self.TwoPiTimeChanged)
        self.PiTimeBox = QtGui.QDoubleSpinBox()
        self.PiTimeBox.setDecimals(6)
        self.PiTimeBox.setRange(xmin,xmax)
        self.connect(self.PiTimeBox, QtCore.SIGNAL('editingFinished()'), self.PiTimeChanged)
        self.PiOverTwoTimeBox = QtGui.QDoubleSpinBox()
        self.PiOverTwoTimeBox.setDecimals(6)
        self.PiOverTwoTimeBox.setRange(xmin,xmax)
        self.connect(self.PiOverTwoTimeBox, QtCore.SIGNAL('editingFinished()'), self.PiOverTwoTimeChanged)
                
    def setRanges(self):
        xmin, xmax = self.parent.parent.qmc.getDataXLimits()
        self.minRange = QtGui.QDoubleSpinBox()
        self.minRange.setDecimals(6)
        self.minRange.setRange(xmin, xmax)
        self.minRange.setValue(xmin)
        self.minRange.setSingleStep(.1)
        self.minRange.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.minRange.setKeyboardTracking(False)
        self.connect(self.minRange, QtCore.SIGNAL('valueChanged(double)'), self.minRangeSignal)
        self.maxRange = QtGui.QDoubleSpinBox()
        self.maxRange.setDecimals(6)
        self.maxRange.setRange(xmin, xmax)
        self.maxRange.setValue(xmax)
        self.maxRange.setSingleStep(.1)
        self.maxRange.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.maxRange.setKeyboardTracking(False)  
        self.connect(self.maxRange, QtCore.SIGNAL('valueChanged(double)'), self.maxRangeSignal)
        
    def minRangeSignal(self, evt):
        self.minRange.setRange(self.minRange.minimum(), self.maxRange.value())
    def maxRangeSignal(self, evt):
        self.maxRange.setRange(self.minRange.value(), self.maxRange.maximum())

    def setupParameterTable(self, curveName):
        self.curveName = str(curveName)
        
        # clear the existing widgets      
        self.parameterTable.clear()
        self.parameterTable.setHorizontalHeaderLabels(QtCore.QStringList(['Fit','Parameters','Manual','Fitted']))
        self.parameterTable.horizontalHeader().setStretchLastSection(True)
#        self.parameterTable.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem('Parameters'))
#        self.horizontalHeader = self.parameterTable.horizontalHeader()
        
        self.parameterLabels = {}
        self.parameterSpinBoxes = {}
        self.FitParameterBox={}
        self.parameterTable.setRowCount(len(self.fitCurveDictionary[self.curveName].parameterNames))

        try:
            test = self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName]
        except:
            # no previously saved parameters, create them
            self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName] = [{}, {}]
            for parameterName, parameterValue in zip(self.fitCurveDictionary[self.curveName].parameterNames, self.fitCurveDictionary[self.curveName].parameterValues):
                # perhaps there are starting parameters already specified
                try:
                    self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0][parameterName] = parameterValue
                    self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1][parameterName] = parameterValue
                except:
                    print 'Parameters must have a default fitting value!'
                    
        i = 0

        for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
            # Create things
            self.parameterLabels[parameterName] = QtGui.QLabel(parameterName)
            self.parameterLabels[parameterName].setAlignment(QtCore.Qt.AlignCenter)
            self.parameterSpinBoxes[parameterName] = QtGui.QDoubleSpinBox()
            self.parameterSpinBoxDict[self.parameterSpinBoxes[parameterName]] = parameterName
            self.parameterSpinBoxes[parameterName].setDecimals(6)
            self.parameterSpinBoxes[parameterName].setRange(-1000000000, 1000000000)
            self.parameterSpinBoxes[parameterName].setValue(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0][parameterName])                
            self.parameterSpinBoxes[parameterName].setSingleStep(.1)
            self.parameterSpinBoxes[parameterName].setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
            self.parameterSpinBoxes[parameterName].setKeyboardTracking(False)
            self.connect(self.parameterSpinBoxes[parameterName], QtCore.SIGNAL('valueChanged(double)'), self.drawCurvesSignal)
            
            self.parameterTable.setCellWidget(i, 1, self.parameterLabels[parameterName])
            self.parameterTable.setCellWidget(i, 2, self.parameterSpinBoxes[parameterName])
            item = QtGui.QTableWidgetItem()
            item.setText(str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1][parameterName]))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.parameterTable.setItem(i, 3, item)
            
            self.FitParameterBox[parameterName] = QtGui.QTableWidgetItem()
            self.FitParameterBox[parameterName].setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            if self.fitCurveDictionary[self.curveName].parameterFit[i]==True:
                self.FitParameterBox[parameterName].setCheckState(QtCore.Qt.Checked)
            else:
                self.FitParameterBox[parameterName].setCheckState(QtCore.Qt.Unchecked)
            self.parameterTable.setItem(i,0,self.FitParameterBox[parameterName])
            i += 1
        
        self.manualTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0].values()) + '\']')
        self.fittedTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1].values()) + '\']')
#        self.connect(self.parameterTable,QtCore.SIGNAL('itemClicked(QListWidgetItem*)'),self.test)
        self.parameterTable.itemClicked.connect(self.updateParameterFit)
        if self.curveName not in ['Cosine','Ramsey Fringes','Rabi Flop']:
            hideit=True
            self.guessfrabiButton.setHidden(True)
        else:
            hideit=False
            if self.curveName == 'Rabi Flop': self.guessfrabiButton.setHidden(False)
            else: self.guessfrabiButton.setHidden(True)
            self.setPiTimeBoxes(0) 
        self.TwoPiTimeBox.setHidden(hideit)
        self.TwoPiLabel.setHidden(hideit)
        self.PiTimeBox.setHidden(hideit)
        self.PiLabel.setHidden(hideit)
        self.PiOverTwoTimeBox.setHidden(hideit)
        self.PiOverTwoLabel.setHidden(hideit)
       
#        self.resize(self.sizeHint())
        self.resizeWindow()
#        self.adjustSize()      
        
    def getParameter(self,which=0):#which = 0 for manual parameters, 1 for fitted parameters
        params=[]
        for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
            params.append(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][which][parameterName])
        return params    
    
    def onActivated(self):
        # this is where we remake the grid, yea just remake it, let's make a function
        self.setupParameterTable(self.combo.currentText()) 
        
    def fitCurveSignal(self, evt):
        self.fitCurves()
        
    def updateParameterFit(self,evt):
        i=0
        for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
            if self.FitParameterBox[parameterName].checkState()==2:
                self.fitCurveDictionary[self.curveName].parameterFit[i]=True
            else:
                self.fitCurveDictionary[self.curveName].parameterFit[i]=False
            i+=1
        
    def TwoPiTimeChanged(self):
        value = self.TwoPiTimeBox.value()
        self.updatePiTime(value)
    
    def PiTimeChanged(self):
        value = self.PiTimeBox.value()
        self.updatePiTime(2.0*value)
    
    def PiOverTwoTimeChanged(self):
        value = self.PiOverTwoTimeBox.value()
        self.updatePiTime(4.0*value)    
        
    def setRabiFrequencyFromPiTime(self,twopitime):
        if self.curveName == 'Rabi Flop':
                # create reasonable guess for rabi frequency based on sideband, trap_frequency
                trap_frequency=self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, 'Rabi Flop'][0]['Trap Frequency']
                sideband_order=self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, 'Rabi Flop'][0]['Sideband']
                nmax=self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, 'Rabi Flop'][0]['nmax']
                # call time evolution via fitRabiflop to get lamb-dicke parameter
                import timeevolution as te
                from labrad import units as U
                eta=te.time_evolution(U.WithUnit(trap_frequency,'MHz'),sideband_order,nmax).eta
                self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0]['Rabi Frequency']=1.0/((2.0*eta)**np.abs(sideband_order)*twopitime*10**-6)
                self.fitCurves(parameters = self.getParameter(),drawCurves = True)
                self.onActivated() 
    
    def updatePiTime(self,twopitime):
        if not twopitime == 0:
            if self.curveName in ['Cosine','Ramsey Fringes']:
                self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0]['Frequency']=1.0/(twopitime*10**-6)
                self.fitCurves(parameters = self.getParameter(),drawCurves = True)
                self.onActivated()
            elif self.curveName == 'Rabi Flop': print 'Please use Estimate f_Rabi Button to guess f_Rabi from Pi-Time'
            else: print 'These spin boxes should be hidden if any curve other than Rabi Flop/Cosine/Ramsey Fringe is selected'
        
    def drawCurvesSignal(self, evt):
        sender = self.sender()
        self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0][self.parameterSpinBoxDict[sender]] = sender.value()
        self.manualTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][0].values()) + '\']')
        self.fitCurves(drawCurves = True)

    def setPiTimeBoxes(self,which):
        # UPDATE Pi-TIME SPIN BOXES
        if self.curveName=='Rabi Flop':
            dataX, dataY = self.fitRabiflop.getData(self.dataset, self.directory, self.index)
            params = self.getParameter(which)
            detailedX = np.linspace(dataX.min(),dataX.max(),1000)
            dataY = self.fitRabiflop.fitFunc(detailedX, params)
            m=pylab.unravel_index(np.array(dataY).argmax(), np.array(dataY).shape)
            piTime=detailedX[m]
            self.TwoPiTimeBox.setValue(2.0*piTime)
            self.PiTimeBox.setValue(piTime)
            self.PiOverTwoTimeBox.setValue(piTime/2.0)

        if self.curveName in ['Cosine','Ramsey Fringes']:
            f=self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][which]['Frequency']
            self.TwoPiTimeBox.setValue(1.0/f*10**6)
            self.PiTimeBox.setValue(0.5/f*10**6)
            self.PiOverTwoTimeBox.setValue(0.25/f*10**6)
        
    def fitCurves(self, parameters = None, drawCurves = False):
        labels = self.parent.parent.qmc.datasetLabelsDict[self.dataset, self.directory]
        self.fitCurveDictionary[self.curveName].fitCurve(self.dataset, self.directory, self.index, labels[self.index], parameters, drawCurves)
        # now the solutions (dictionary) should be set, so we use them to fill the 3rd column
        if (drawCurves == False):
            i = 0
            for parameterName in self.fitCurveDictionary[self.curveName].parameterNames:
                self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1][parameterName] = self.solutionsDictionary[self.dataset, self.directory, self.index, self.curveName][i]
                i += 1
            for solution in self.solutionsDictionary[self.dataset, self.directory, self.index, self.curveName]:
                item = QtGui.QTableWidgetItem()
                item.setText(str(solution))
                item.setFlags(QtCore.Qt.ItemIsEditable)
                self.parameterTable.setItem(i, 2, item)
                i += 1
            i = 0
#            self.fittedTextBox.setText('\'Fit\', [\''+str(self.index)+'\', \''+ self.curveName + '\', ' + '\'' + str(self.parent.savedAnalysisParameters[self.dataset, self.directory, self.index, self.curveName][1].values()) + '\']')    
            self.onActivated()
            self.setPiTimeBoxes(1)
        self.resizeWindow()
        
    def guessfrabiClicked(self,evt):
        self.guessfrabiWindow=getfrabiwindow.GuessRabiFrequency(self,self.TwoPiTimeBox.value())
        
    @inlineCallbacks
    def createContext(self):
        self.context = yield self.cxn.context()


    @inlineCallbacks
    def acceptManualSignal(self, evt):
        yield self.parent.parent.parent.cxn.data_vault.cd(self.directory, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.open(self.dataset, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.add_parameter_over_write('Accept-' + str(self.index), True, context = self.context)
        # the fitted solutions are already in data vault, this would overwrite them with the manual
        solutions = []
        for c in range(self.parameterTable.rowCount()):
            solutions.append(self.parameterTable.cellWidget(c, 2).value())
        yield self.parent.parent.parent.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(self.index)+'-'+self.curveName, solutions, context = self.context)
        self.close()

    @inlineCallbacks
    def acceptFittedSignal(self, evt):
        yield self.parent.parent.parent.cxn.data_vault.cd(self.directory, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.open(self.dataset, context = self.context)
        yield self.parent.parent.parent.cxn.data_vault.add_parameter_over_write('Accept-' + str(self.index), True, context = self.context)
        self.close()
        
       
    def resizeWindow(self):
        oldSize = self.parameterTable.sizeHint() # qsize
#        print 'old: ', oldSize
        self.parameterTable.resizeColumnsToContents()
        self.parameterTable.resizeRowsToContents()
        w = 0
        for c in range(self.parameterTable.columnCount()):
            w = w + self.parameterTable.columnWidth(c)
        w = w + self.parameterTable.verticalHeader().width() + self.parameterTable.autoScrollMargin()
        h = 0
        for c in range(self.parameterTable.rowCount()):
            h = h + self.parameterTable.rowHeight(c)
        h = h + self.parameterTable.horizontalHeader().height() + 5
        
#        print 'new w and h: ', w, h
        finalSize = QtCore.QSize()
        sizeHint = self.sizeHint()
        sizeW = sizeHint.width()
        sizeH = sizeHint.height()

#        print 'hint: ', sizeHint
        finalSize.setWidth(sizeW + (w - oldSize.width()))
        finalSize.setHeight(sizeH + (h - oldSize.height()))
#        print 'final: ', finalSize
        self.resize(finalSize)
    
    def closeEvent(self, evt):
        self.parent.analysisWindows.pop((self.dataset, self.directory, self.index,))