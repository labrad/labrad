import matplotlib.pyplot as plt
from PyQt4 import QtGui, QtCore
import os
import datetime
#import labrad
from numpy import array
from twisted.internet.defer import inlineCallbacks

class plotwikidata(QtGui.QWidget):
    
    def __init__(self, data, datadir, parent=None):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle('Wiki Client')
        self.datadir = datadir
        self.data = data
        self.timetag = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.labels =['Title', 'x min','x max','y min',
                       'y max','x label','y label']
        self.xlabel = ''
        self.ylabel = ''
        self.title  = ''
        self.connect()
               
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name='Plot Wiki Data Client')
        self.dv = yield self.cxn.data_vault
        self.ws = yield self.cxn.wikiserver
        yield self.cxn.registry.cd(['','Servers', 'wikiserver'])
        self.wikikey = yield self.cxn.registry.get('wikipath')
        self.maindir = self.wikikey[1] + '/'
        yield os.chdir(self.maindir)
        self.setupWidget()
        
    def setupWidget(self):
        self.setGeometry(300, 300, 750, 300)
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(5)
        self.labeldict = {}
        for i, label in enumerate(self.labels):
            self.labeldict[label] = QtGui.QLabel(self)
            self.labeldict[label].setText(label)
            self.grid.addWidget(self.labeldict[label]     ,0,i)
        
        self.textdict = {}    
        for i, label in enumerate(self.labels):
            self.textdict[label] = QtGui.QLineEdit(self)
            self.grid.addWidget(self.textdict[label]      ,1,i)
        
        self.commentbox = QtGui.QPlainTextEdit(self)
        
        self.gobutton = QtGui.QPushButton('GO!',self) 
        self.gobutton.clicked.connect(self.onbuttonpress)
        
        self.grid.addWidget(self.gobutton      ,0,7,2,2)
        self.grid.addWidget(self.commentbox    ,2,0,2,7)
        self.setLayout(self.grid)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.setWindowTitle("Plot data for Wiki")
        self.show()
        
    def onbuttonpress(self):
        
        self.title     = self.textdict['Title'].text()
        self.xscalemin = self.textdict['x min'].text() 
        self.xscalemax = self.textdict['x max'].text()
        try:
            self.xlims = [float(self.xscalemin),float(self.xscalemax)]
        except: self.xlims = None
        self.yscalemin = self.textdict['y min'].text()
        self.yscalemax = self.textdict['y max'].text()
        try:
            self.ylims = [float(self.yscalemin),float(self.yscalemax)]
        except:
            self.ylims = None
        self.xlabel= self.textdict['x label'].text()
        self.ylabel= self.textdict['y label'].text()
        self.comments = self.commentbox.toPlainText().split('/n')
        self.comments = str(self.comments[0])
        self.get_data()
    
    @inlineCallbacks     
    def get_data(self):
        
        yield self.dv.cd(self.datadir)
        yield self.dv.open(self.data)
        self.dataarray = yield self.dv.get()
        self.dataarray = self.dataarray.asarray
        self.plotdata(self.dataarray)
    @inlineCallbacks
    def plotdata(self, dataarray):
        plt.plot(dataarray[:,0],dataarray[:,1])
        plt.title(self.title)
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        if self.xlims != None:
            plt.xlim(self.xlims)
        if self.ylims != None:
            plt.ylim(self.ylims)
        plt.savefig(self.timetag)
        plt.show()
        yield self.ws.add_line_to_file( self.comments)
        yield self.ws.add_line_to_file( self.timetag + '[[' + self.timetag + '.png]]')
        yield self.ws.update_wiki()
        self.close()