'''
DataVault browser widget
'''
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtCore, QtGui

class DataVaultWidget(QtGui.QListWidget):

    def __init__(self, parent, context):
        QtGui.QListWidget.__init__(self)
        self.parent = parent
        self.context = context

    @inlineCallbacks
    def populateList(self):
        self.clear()
        self.currentDirectory = yield self.parent.parent.server.cd(context = self.context)
        self.currentDirectory = tuple(eval(str(self.currentDirectory)))
        self.addItem(str(self.currentDirectory))
        self.addItem('..')
        self.fileList = yield self.parent.parent.server.dir(context = self.context)
           
        # add sorted directories
        for i in self.sortDirectories():
            self.addItem(i)
        # add sorted datasets
        for i in self.sortDatasets():
            self.addItem(i)

    def sortDirectories(self):
        self.directories = []
        for i in range(len(self.fileList[0])):
            self.directories.append(self.fileList[0][i])
        if self.directories:
            self.directories.sort()
        return self.directories
    
    def sortDatasets(self):
        self.datasets = []
        for i in range(len(self.fileList[1])):
            self.datasets.append(self.fileList[1][i])
        if self.datasets:
            self.datasets.sort()
        return self.datasets

    def addDatasetItem(self, itemLabel, directory):
        if (directory == self.currentDirectory):
            self.addItem(itemLabel)
            self.datasets.append(itemLabel)

#        # configure the items list
#        self.setViewMode(QtGui.QListView.IconMode)
#        self.setLayoutMode(QtGui.QListView.SinglePass)
#        self.setResizeMode(QtGui.QListView.Adjust)
#        self.setGridSize(QtCore.QSize(75, 75))
#    
#    def mouseReleaseEvent(self, event):
#        """
#        mouse button release event
#        """
#        button = event.button()
#        # select an item on which we clicked
#        item = self.itemAt(event.x(), event.y())
#        if item:
#            self.setCurrentItem(item)
#            if button == 1:
#                print 'SIMPLE LEFT CLICK'
#    
    @inlineCallbacks
    def changeDirectory(self, directory):
        yield self.parent.parent.server.cd(directory, context = self.context)
        self.populateList()

    
    def mousePressEvent(self, event):
        """
        mouse clicks events
        """
        button = event.button()
        item = self.itemAt(event.x(), event.y())
        if item:
            if (item == self.item(1)):
                if (button == 1):
                    self.changeDirectory(1)
            elif (str(item.text()) in self.directories):
                # select the item we clicked
                self.setCurrentItem(item)
                if (button == 1):
                    self.changeDirectory(str(item.text()))
            elif (str(item.text()) in self.datasets):
                itemText = item.text()
                dataset = int(str(itemText)[0:5]) # retrieve dataset number
                datasetName = str(itemText)[8:len(itemText)]
                if (button == 1):
                    manuallyLoaded = True
                    self.parent.parent.newDataset(dataset, self.currentDirectory, manuallyLoaded, datasetName)       
                elif (button == 2):
                    #keys = self.parent.parent.datasetDict.keys()    
                    if self.parent.parent.datasetDict.has_key((dataset, self.currentDirectory)):
                        self.parent.newParameterWindow(dataset, self.currentDirectory)
                    



