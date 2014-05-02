from PyQt4 import QtGui
from connectedLayoutWidget import connectedLayoutWidget
from signalWidget import signalWidget

class combinedWidget(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(combinedWidget, self).__init__(parent)
        self.reactor = reactor
        self.create_layout()
    
    def create_layout(self):
        '''
        creates a vertical layout of two widgets
        '''
        self.setWindowTitle('Combined Widget')
        layout = QtGui.QVBoxLayout()
        connected_w = connectedLayoutWidget(reactor)
        signaling_w = signalWidget(reactor)
        layout.addWidget(connected_w)
        layout.addWidget(signaling_w)
        self.setLayout(layout)
        
    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    clipboard = a.clipboard()
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    combinedWidget = combinedWidget(reactor)
    combinedWidget.show()
    reactor.run()