from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui

class sampleWidget(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(sampleWidget, self).__init__(parent)
        self.reactor = reactor
        self.setWindowTitle('Sample Widget')
        self.connect()
    
    @inlineCallbacks
    def connect(self):
        #make an asynchronous connection to LabRAD
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name = 'Sample Widget')
    
    def closeEvent(self, x):
        #stop the reactor when closing the widget
        self.reactor.stop()

if __name__=="__main__":
    #join Qt and twisted event loops
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = sampleWidget(reactor)
    widget.show()
    reactor.run()