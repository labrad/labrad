from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.internet.error import ConnectionRefusedError
from grapherwindow import FirstWindow, GrapherWindow
from dataset import Dataset
from histogram import HistWindow
import sys
import time
import gc

MAXWINDOWS = 10
GraphRefreshTime = .1; # s, how often the plot updates

class COMMUNICATE(QtCore.QObject):
    
    connectionReady = QtCore.pyqtSignal()

class CONNECTIONS(QtGui.QGraphicsObject):
    '''
    The CONNECTIONS serves as a mediator between the Dataset class and the GrapherWindow  class. 
    
    A grapher works by keeping track of datasets and determining which windows
    to plot them on. The main dictionary, dwDict, relates Dataset objects with GrapherWindow
    objects. Each time a new dataset is created, CONNECTIONS creates a unique 
    Dataset object. It then determines which GrapherWindow objects the dataset should
    be drawn on. i.e.:
    
        Without dataset overlaying (dwDict):
        
            [Dataset1] = [GrapherWindow1]
            [Dataset2] = [GrapherWindow2]
            [Dataset3] = [GrapherWindow3]
                       .
                       .
                       .
    
        With dataset overlaying (dwDict):

            [Dataset1] = [GrapherWindow1, GrapherWindow3]
            [Dataset2] = [GrapherWindow2]
            [Dataset3] = [GrapherWindow3, GrapherWindow2]
                       .
                       .
                       .
    
    GrapherWindow objects are added and removed from the dictionary depending on factors
    such as overlaying datasets or closing windows.
    
    Note: the grapher will only plot datasets that possess the 'plotLive' parameter. This 
    parameter is checked for in the Dataset class. This prevents unwanted new datasets from being plotted
    Old datasets that are manually loaded from graph are exempt from this requirement.
    
    There is a main timer event that retrieves data from the Dataset buffer, sends it to
    the GrapherWindow, and calls on GrapherWindow to draw the plot. This ensures that all datasets
    are plotted constantly in order to maintain a live update.     

    '''

    def __init__(self, reactor, parent=None):
        super(CONNECTIONS, self).__init__()
        self.reactor = reactor
        self.dwDict = {} # dictionary relating Dataset and ApplicationWindow
        self.datasetDict = {} # dictionary relating a Dataset object with the dataset and directory 
#        self.winList = []
        self.histList = []
        self.windowCounter = 0
        self.winDict = {}
        self.attemptLabRadConnect()               
        self.startTimer()
        self.communicate = COMMUNICATE()

    def attemptLabRadConnect(self):
        from labrad.errors import LoginFailedError
        deferred = self.connectLabRAD()
        def handleLabRadError(failure):
            if (failure.trap(ConnectionRefusedError)):
                self.retryLabradConnectDialog = RetryConnectingDialog(self, 'LabRAD')
                self.retryLabradConnectDialog.show()
        deferred.addErrback(handleLabRadError)

    def attemptDataVaultConnect(self):
        deferred = self.connectDataVault()
        def handleDataVaultError(failure):
            if (failure.trap(AttributeError)):
                self.retryLabradConnectDialog = RetryConnectingDialog(self, 'DataVault')
                self.retryLabradConnectDialog.show()
        deferred.addErrback(handleDataVaultError)

    # connect to the data vault    
    @inlineCallbacks    
    def connectLabRAD(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        try: # if the connection failed and was retried, close the dialog
            self.retryLabradConnectDialog.close()
        except AttributeError:
            pass
        self.cxn = yield connectAsync(name='PyGrapherLive')
        self.attemptDataVaultConnect()

    @inlineCallbacks
    def connectDataVault(self):
        try: # if the connection failed and was retried, close the dialog
            self.retryLabradConnectDialog.close()
        except AttributeError:
            pass
        self.server = yield self.cxn.data_vault
        yield self.setupListeners()
        context = yield self.cxn.context() # create a new context
        self.introWindow = FirstWindow(self, context, self.reactor)
        self.introWindow.show()
        print 'Connection established: now listening dataset.'
        self.communicate.connectionReady.emit()
        
        
        
    # set up dataset listener    
    @inlineCallbacks
    def setupListeners(self):               
        yield self.server.signal__new_dataset_dir(88888)#, context = context)
        yield self.server.addListener(listener = self.updateDataset, source = None, ID = 88888)#, context = context)    
        yield self.server.signal__new_directory(77777)#, context = context)
        yield self.server.addListener(listener = self.addDirItem, source = None, ID = 77777)#, context = context)
        yield self.server.signal__new_parameter_dataset(99999)#, context = context)
        yield self.server.addListener(listener = self.updateParameter, source = None, ID = 99999)#, context = context)    

    def addDirItem(self,x,y):
        #directory = tuple(eval(str(y))) 
        self.introWindow.datavaultwidget.populateList()
#        for i in self.winDict.values():
#            i.datavaultwidget.populateList()
#        for i in self.winList:
#            i.datavaultwidget.populateList()
           
    # new dataset signal
    def updateParameter(self,x,y):
        dataset = y[0]
        datasetName = y[1]
#        print datasetName
        directory = y[2]
        itemLabel = (str(dataset) + ' - ' + str(datasetName))
        # process parameter 
        if (y[3] == 'plotLive'):
            manuallyLoaded = False # ensure that this dataset was not loaded manually
            self.newDataset(dataset, directory, manuallyLoaded, datasetName)
        elif (y[3] == 'Histogram'):
            self.createHistogram(dataset, directory, datasetName)
        elif (y[3] == 'Fit'):
            try:
                self.datasetDict[dataset, directory].fit()
            except:
                print 'Was plotLive set for this dataset?'

    def updateDataset(self, x, y):
#        dataset = int(y[0][0:5]) # retrieve dataset number
#        datasetName = str(y[0][8:len(y[0])])
#        print datasetName
        directory = y[1] # retrieve directory
        itemLabel = y[0] # 'dataset - datasetName' 
        self.addDatasetItem(itemLabel, directory)
#        print directory
#        print dataset
#        print x, y
 
    def addDatasetItem(self, itemLabel, directory):
        self.introWindow.datavaultwidget.addDatasetItem(itemLabel, directory)
#        for i in self.winDict.values():
#            i.datavaultwidget.addDatasetItem(itemLabel, directory)
#        for i in self.winList:
#            i.datavaultwidget.addDatasetItem(itemLabel, directory)
 
    @inlineCallbacks
    def createHistogram(self, dataset, directory, datasetName):
        
        context = yield self.cxn.context()
        yield self.server.cd(directory, context=context)
        yield self.server.open(dataset, context=context)
            
        threshold = yield self.server.get_parameter('Histogram', context=context)
        Data = yield self.server.get(context=context)
        data = Data.asarray
        
        histWindow = HistWindow(self, data, threshold, datasetName)
        self.histList.append(histWindow)
        histWindow.show()        
    
    # Creates a new Dataset object and checks if it has the 'plotLive' parameter
    @inlineCallbacks
    def newDataset(self, dataset, directory, manuallyLoaded, datasetName):
        context = yield self.cxn.context() # create a new context
        datasetObject = Dataset(self, self.cxn, context, dataset, directory, datasetName, self.reactor)
        self.datasetDict[dataset, directory] = datasetObject
        yield datasetObject.openDataset(context)
#        yield datasetObject.setupParameterListener(context)
#        yield datasetObject.checkForPlotParameter()
        datasetLabels = yield datasetObject.getYLabels()
        windowName = []
        if (len(self.winDict.values()) < MAXWINDOWS):
            # if the dataset was loaded manually, it does not require the 'Window' parameter 
            if (manuallyLoaded == True):
                try:
                    histValue = yield self.server.get_parameter('Histogram', context = context)
                    self.createHistogram(dataset, directory, datasetName)
                    datasetObject.endTimer()
                    del datasetObject
                except:
                    self.prepareDataset(datasetObject, dataset, directory, datasetLabels, windowName)#, context)
            else:        
#               hasPlotParameter = yield datasetObject.listenForPlotParameter()
#               if (hasPlotParameter == True):
                windowParameter = yield datasetObject.getWindowParameter()
                # if windows are specified (via parameter), send that instead
                if (windowParameter != None):
                    self.prepareDataset(datasetObject, dataset, directory, datasetLabels, windowParameter)#, context)
                else:
                    self.prepareDataset(datasetObject, dataset, directory, datasetLabels, windowName)#, context)
#            else:
#                    # This data is not for plotting. Remove it.
#                    # There should be a cleaner way of doing this
#                    datasetObject.endTimer()
#                    del datasetObject
        else:
            print 'Too many windows open!'
            datasetObject.endTimer()
            del datasetObject

    # Prepare the dataset for plotting
    @inlineCallbacks
    def prepareDataset(self, datasetObject, dataset, directory, datasetLabels, windowNames):#, context):      
        #if windows request overlay, update those. else, create a new window.
        overlayWindows = self.getOverlayingWindows()
        overlayWindowNames = []
        if overlayWindows:
            # if the dataset is already in the window
            overlayWindows = [x for x in overlayWindows if ((dataset, directory) not in x.qmc.dataDict.keys())]
            for overlayWindow in overlayWindows:
                overlayWindow.qmc.initializeDataset(dataset, directory, datasetLabels)
#                overlayWindow.createDatasetCheckbox(dataset, directory)
                overlayWindowNames.append(overlayWindow.windowName)
            if overlayWindows:
                self.dwDict[datasetObject] = overlayWindows
        elif (len(windowNames) == 0):
            windowName = 'Window ' + str(self.windowCounter)
            self.windowCounter = self.windowCounter + 1
            context = yield self.cxn.context() # create a new context
            win = self.newGraph(context, windowName)
            yield deferToThread(time.sleep, .01)
            self.dwDict[datasetObject] = [win]
            win.qmc.initializeDataset(dataset, directory, datasetLabels)
#            win.createDatasetCheckbox(dataset, directory)
                    
        # process windowNames that came from parameters (the following won't happen without window parameters specified)
        for windowName in windowNames:
            if windowName in overlayWindowNames:
                pass
            # if the window is open and it isn't asking for overlay    
            elif windowName in self.winDict.keys():
                try:
                    self.dwDict[datasetObject].append(self.winDict[windowName])
                except KeyError:
                    self.dwDict[datasetObject] = [self.winDict[windowName]]    
                self.winDict[windowName].qmc.initializeDataset(dataset, directory, datasetLabels)
#                self.winDict[windowName].createDatasetCheckbox(dataset, directory)
            else:
                context = yield self.cxn.context() # create a new context
                win = self.newGraph(context, windowName)
                yield deferToThread(time.sleep, .01)
                try:
                    self.dwDict[datasetObject].append(win)
                except KeyError:
                    self.dwDict[datasetObject] = [win]    
                win.qmc.initializeDataset(dataset, directory, datasetLabels)
#                win.createDatasetCheckbox(dataset, directory)

    # create a new graph window
#    def newGraph(self, context, windowName):
    def newGraph(self, context, windowName):
        win = GrapherWindow(self, context, windowName)
        self.winDict[windowName] = win
#        self.winList.append(win)
        win.show()
        return win
            
    def startTimer(self): 
        lc = LoopingCall(self.timerEvent)
        lc.start(GraphRefreshTime)
     
    # Main timer, cycles through dwDict. For each dataset, determines...
    # ... which windows to draw the dataset on. Then draws the plot.   
    @inlineCallbacks
    def timerEvent(self):
#        print 'in connections: {0}'.format( len(self.dwDict.keys()) )
        for datasetObject in self.dwDict.keys():
            windowsToDrawOn = self.dwDict[datasetObject]
            if (datasetObject.data != None):
                data = datasetObject.data
                yield datasetObject.emptyDataBuffer()
                for i in windowsToDrawOn:
#                    print 'still happening connections'
                    i.qmc.setPlotData(datasetObject.dataset, datasetObject.directory, data)
    # Cycles through the values in each key for checked Overlay boxes, returns the windows...
    # ...with the overlay button checked
    def getOverlayingWindows(self):
        self.overlaidWindows = []
        for i in self.dwDict.keys():
            values = self.dwDict[i]
            for j in values:
                if j.cb2.isChecked():
                    # skip duplicates
                    if j in self.overlaidWindows:
                        pass
                    else:
                        self.overlaidWindows.append(j)
        return self.overlaidWindows
    
    @inlineCallbacks
    def getParameters(self, dataset, directory):
        parametersValues = []
        parameters = yield self.cxn.data_vault.parameters(context = self.datasetDict[dataset, directory].context)
        values = []
        for parameter in parameters:
           parameterValue = yield self.cxn.data_vault.get_parameter(parameter, context = self.datasetDict[dataset, directory].context)
           values.append(parameterValue)
        for parameter, value in zip(parameters, values):
            parametersValues.append((parameter, value))
        
        returnValue( parametersValues )
    
    def changeWindowName(self, oldWindowName, newWindowName):
        self.winDict[newWindowName] = self.winDict[oldWindowName]
        del self.winDict[oldWindowName]
        
    
    # Datasets no longer need to be drawn on closed windows
    @inlineCallbacks
    def removeWindowFromDictionary(self, win):
#        print sys.getrefcount(win)
        #objgraph.show_most_common_types(limit=20)
        for i in self.dwDict.keys():
            values = self.dwDict[i]
            for j in values:
                if j == win:
                    # if the last window is being removed, delete the dataset object
                    # from the dictionary
                    if (len(values) == 1):
                        #self.dwDict[i].remove(j)
                        i.endTimer()
                        print 'disconnecting data signal'
                        yield i.disconnectDataSignal()
                        del self.dwDict[i]
                    else:
                        self.dwDict[i].remove(j)

        
    # Datavault widgets no longer need to be updated
    def removeWindowFromWinList(self, win):
        for i in self.winList:
            if i == win:
                self.winList.remove(i)
                
    # Datavault widgets no longer need to be updated
    def removeWindowFromWinDict(self, windowName):
        del self.winDict[windowName]
    
    @inlineCallbacks
    def cleanUp(self):
        print 'clean!'
        yield deferToThread(time.sleep, 5)
        gc.collect()
                
class RetryConnectingDialog(QtGui.QDialog):
    def __init__(self, parent, destination):
        QtGui.QDialog.__init__(self)
        self.parent = parent
        self.destination = destination
        self.setupUi(self)
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.confirmButton = QtGui.QPushButton(Dialog)
        self.confirmButton.setText('Retry')
        self.gridLayout.addWidget(self.confirmButton,1,0)
        self.declineButton = QtGui.QPushButton(Dialog)
        self.declineButton.setText('Exit')
        self.gridLayout.addWidget(self.declineButton,1,1)
        self.label = QtGui.QLabel('Could not connect to ' + str(self.destination) + '!')
        self.font = QtGui.QFont()
        self.font.setPointSize(20)
        self.label.setFont(self.font)
        self.gridLayout.addWidget(self.label,0,0)
        if (self.destination == 'LabRAD'):
            self.confirmButton.clicked.connect(self.parent.attemptLabRadConnect)
        elif (self.destination == 'DataVault'):
            self.confirmButton.clicked.connect(self.parent.attemptDataVaultConnect)
        self.declineButton.clicked.connect(self.parent.reactor.stop)
