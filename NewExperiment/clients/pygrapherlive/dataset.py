'''
The data is assumed to be an array with at least 2 dimensions: a list of x values,
and at least one list of y values.

Data is temporarily stored in a buffer. Once the data is retrieved by the Connections
class, the buffer emptied.

'''

from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from PyQt4 import QtCore
#from twisted.internet.threads import deferToThread
import numpy as np
import time

class Dataset(QtCore.QObject):
    
    """Class to handle incoming data and prepare them for plotting """
    def __init__(self, parent, cxn, context, dataset, directory, datasetName, reactor):
        super(Dataset, self).__init__()
        self.accessingData = DeferredLock()
        self.parent = parent
        self.cxn = cxn
        self.context = context # context of the first dataset in the window
        self.dataset = dataset
        self.datasetName = datasetName
        self.directory = directory
        self.reactor = reactor
        self.data = None
#        self.hasPlotParameter = False
        self.cnt = 0
        self.setupDataListener(self.context)
#        self.setupFitListener(self.context)
        
#    @inlineCallbacks
#    def checkForPlotParameter(self):
#        self.parameters = yield self.cxn.data_vault.get_parameters(context = self.context)
#        if (self.parameters != None):
#            for (parameterName, value) in self.parameters:
#                if (str(parameterName) == 'plotLive'):
#                    self.hasPlotParameter = True
#                elif ((self.hasPlotParameter == True and str(parameterName) == 'Fit')):
#                      self.updateFit()

    @inlineCallbacks
    def getWindowParameter(self):
        try: 
            value = yield self.cxn.data_vault.get_parameter('Window', context = self.context)
        except:
            value = None
        returnValue(value)
                    
    # open dataset in order to listen for new data signals in current context        
    @inlineCallbacks
    def openDataset(self, context):
        yield self.cxn.data_vault.cd(self.directory, context = context)
        yield self.cxn.data_vault.open(self.dataset, context = context)
        self.parameters = yield self.cxn.data_vault.parameters(context = context)
        self.parameterValues = []
        for parameter in self.parameters:
            parameterValue = yield self.cxn.data_vault.get_parameter(parameter, context = context)
            self.parameterValues.append(parameterValue)
    
#    @inlineCallbacks
#    def setupParameterListener(self, context):
#        yield self.cxn.data_vault.signal__new_parameter(66666, context = context)
#        yield self.cxn.data_vault.addListener(listener = self.updateParameter, source = None, ID = 66666, context = context)
    
#    # Over 60 seconds, check if the dataset has the appropriate 'plotLive' parameter            
#    @inlineCallbacks
#    def listenForPlotParameter(self):
#        for i in range(20):
#            if (self.hasPlotParameter == True):
#                returnValue(self.hasPlotParameter)
##            yield deferToThread(time.sleep, .5)
#            yield self.wait(.5)
#        returnValue(self.hasPlotParameter)        
#            
#    def updateParameter(self, x, y):
#        self.checkForPlotParameter()

        #append whatever to self.parameters

#    # sets up the listener for new data
#    @inlineCallbacks
#    def setupFitListener(self, context):
#        yield self.cxn.data_vault.signal__new_parameter(22222, context = context)
#        yield self.cxn.data_vault.addListener(listener = self.updateFit, source = None, ID = 22222, context = context)
    
#    # new data signal
    @inlineCallbacks
#    def updateFit(self):
    def fit(self):        
        value = yield self.cxn.data_vault.get_parameter('Fit', context = self.context)
        variables = yield self.cxn.data_vault.variables(context = self.context)
        numberDependentVariables = len(variables[1])
#       if (self.parameters != None):
        try:
            for window in self.parent.dwDict[self]:
                window.fitFromScript(self.dataset, self.directory, numberDependentVariables, value) 
        except KeyError:
            print 'dwDict not created yet. Either the Fit parameter was added before data was created or the data is added too quickly. Try adding a pause after adding all the data intended for fitting.'
    # sets up the listener for new data
    @inlineCallbacks
    def setupDataListener(self, context):
        yield self.cxn.data_vault.signal__data_available(11111, context = context)
        yield self.cxn.data_vault.addListener(listener = self.updateData, source = None, ID = 11111, context = context)
        #self.setupDeferred.callback(True)
        self.updatecounter = 0
        self.timer = self.startTimer(100)
    
    # new data signal
    def updateData(self,x,y):
        self.updatecounter = self.updatecounter + 1
        self.getData(self.context)
#        print 'still happening dataset'
    
    def timerEvent(self,evt):
        #print self.updatecounter
#        print 'in dataset'
#        if self.updatecounter < 1:
#            print 'slowing down!, less than 1 dataupdate per 100milliseconds '
        self.updatecounter = 0
    
    def endTimer(self):
        self.killTimer(self.timer)

    @inlineCallbacks    
    def disconnectDataSignal(self):
        yield self.cxn.data_vault.removeListener(listener = self.updateData, source = None, ID = 11111, context = self.context)
#        yield self.cxn.data_vault.removeListener(listener = self.updateParameter, source = None, ID = 66666, context = self.context)

    # returns the current data
    @inlineCallbacks
    def getData(self,context):
        Data = yield self.cxn.data_vault.get(100, context = context)
        if (self.data == None):
            self.data = Data.asarray
        else:
            yield self.accessingData.acquire()         
            self.data = np.append(self.data, Data.asarray, 0)
            self.accessingData.release()
        
    @inlineCallbacks
    def emptyDataBuffer(self):
        yield self.accessingData.acquire()
        del(self.data)
        self.data = None
        self.accessingData.release()
    
    @inlineCallbacks
    def getYLabels(self):
        labels = []
        variables = yield self.cxn.data_vault.variables(context = self.context)
        for i in range(len(variables[1])):
            labels.append(variables[1][i][1] + ' - ' + self.datasetName)
        returnValue(labels)
            
    def wait(self, seconds, result=None):
        d = Deferred()
        self.reactor.callLater(seconds, d.callback, result)
        return d    
