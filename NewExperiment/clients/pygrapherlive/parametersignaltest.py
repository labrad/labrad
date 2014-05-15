from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.internet.error import ConnectionRefusedError
from connections import CONNECTIONS


class CONNECTIONS(QtGui.QGraphicsObject):

    def __init__(self, reactor, parent=None):
        super(CONNECTIONS, self).__init__()
        self.reactor = reactor
        self.connect()
        
    # connect to the data vault    
    @inlineCallbacks    
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.data_vault
        yield self.setupListeners()

        
    # set up dataset listener    
    @inlineCallbacks
    def setupListeners(self):               
        yield self.server.signal__new_parameter_dataset(99999)#, context = context)
        yield self.server.addListener(listener = self.updateDataset, source = None, ID = 99999)#, context = context)    

    def updateDataset(self, x, y):
        print x
        print y


if __name__ == '__main__':
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    Connections = CONNECTIONS(reactor)
    reactor.run()