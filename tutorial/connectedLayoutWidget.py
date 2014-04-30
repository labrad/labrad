from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui

class connectedLayoutWidget(QtGui.QWidget):
    def __init__(self, reactor, parent=None):
        super(connectedLayoutWidget, self).__init__(parent)
        self.reactor = reactor
        self.setupLayout()
        self.connect()
    
    def setupLayout(self):
        #setup the layout and make all the widgets
        self.setWindowTitle('Connected Layout Widget')
        #create a horizontal layout
        layout = QtGui.QHBoxLayout()
        #name of the parameter
        self.lineedit = QtGui.QLineEdit()
        #value entry
        self.spin = QtGui.QDoubleSpinBox()
        #buttons for submitting
        self.submit = QtGui.QPushButton('Submit')
        #add all the button to the layout
        layout.addWidget(self.lineedit)
        layout.addWidget(self.spin)
        layout.addWidget(self.submit)
        self.setLayout(layout)
        
    @inlineCallbacks
    def connect(self):
        #make an asynchronous connection to LabRAD
        from labrad.wrappers import connectAsync
        from labrad.errors import Error
        self.Error = Error
        cxn = yield connectAsync(name = 'Connected Layout Widget')
        self.registry = cxn.registry
        self.lineedit.editingFinished.connect(self.on_editing_finished)
        self.submit.pressed.connect(self.on_submit)
    
    @inlineCallbacks
    def on_submit(self):
        '''
        when the submit button is pressed, submit the value to the registry
        '''
        text = self.lineedit.text()
        value = self.spin.value()
        key = str(text) #convert QString to python string
        yield self.registry.set(key, value)
        
    @inlineCallbacks
    def on_editing_finished(self):
        '''
        called when the user is finished edintg the parameter name
        tries to load the value from the registry, if it's there
        '''
        text = self.lineedit.text()
        key = str(text) #convert QString to python string
        try:
            value = yield self.registry.get(key)
        except self.Error as e:
            print e
        else:
            self.spin.setValue(value)
        
    def closeEvent(self, x):
        #stop the reactor when closing the widget
        self.lineedit.editingFinished.disconnect()
        self.reactor.stop()

if __name__=="__main__":
    #join Qt and twisted event loops
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = connectedLayoutWidget(reactor)
    widget.show()
    reactor.run()