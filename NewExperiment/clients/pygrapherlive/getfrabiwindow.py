'''
Created on Mar 12, 2013

@author: Lab-user
'''
from PyQt4 import QtCore, uic
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"Views", "guessfrabi.ui")
base, form = uic.loadUiType(path)

class GuessRabiFrequency(base, form):
    def __init__(self,parent,twopitime):
        super(GuessRabiFrequency, self).__init__()
        self.parent=parent
        self.twopitime=twopitime
        self.setupUi(self)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Guess f-Rabi')
        self.PiTimeSpinBox.setValue(self.twopitime)
        self.PiTimeSpinBox.setDecimals(6)
        self.PiTimeSpinBox.setRange(0,1000000000000)
        self.connect(self.PiTimeSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.SpinBoxChanged)
        self.show()
        
        self.comboBox.activated[str].connect(self.onActivated)
        self.comboBox.setCurrentIndex(1)
        self.okButton.clicked.connect(self.okButtonClicked)
        self.onActivated()
        
    def SpinBoxChanged(self,evt):
        self.twopitime=self.factor*evt
        
    def onActivated(self):
        if self.comboBox.currentIndex()==0: self.factor=1.0
        elif self.comboBox.currentIndex()==1: self.factor=2.0
        elif self.comboBox.currentIndex()==2: self.factor=4.0
        self.PiTimeSpinBox.setValue(self.twopitime/self.factor)
        
    def okButtonClicked(self):
        self.parent.setRabiFrequencyFromPiTime(self.twopitime)
        self.parent.guessfrabiWindow=None