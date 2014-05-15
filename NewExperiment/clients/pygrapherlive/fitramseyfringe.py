"""
This class defines Ramsey Fringes to fit and its parameters
"""
import numpy as np
from fitcurve import CurveFit

class FitRamseyFringe(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Ramsey Fringes'
        self.parameterNames = [ 'Frequency','T2','Phase','Contrast','Offset']
        self.parameterValues = [50000.0,0.002,0.0,1.0,0.0]
        self.parameterFit = [True,True,True,True,True]
   
    def fitFunc(self, x, p):      
        x=x*10**-6
        evolution = p[3]*np.exp(-x/p[1])*(np.cos(np.pi*p[0]*x+p[2]*np.pi)**2-.5)+.5+p[4]
        return evolution