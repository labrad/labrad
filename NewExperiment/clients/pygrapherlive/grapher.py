'''
Live Grapher for Pylabrad Version 5.0

Overview:

All data comes from the Labrad Data Vault. The grapher uses modified version of the
data vault, which utilizes a custom new dataset signal.

The grapher is composed of three parts: Connections, Dataset, and the Grapher
Window. The grapher listens for new datasets, creates a Dataset object to 
handle incoming data, and creates the Grapher Window to plot the data. The
grapher facilitates the transfer of old and live data to the grapher window.

'''

from PyQt4 import QtGui
from connections import CONNECTIONS

if __name__ == '__main__':
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    Connections = CONNECTIONS(reactor)
    reactor.run()