"""
This class defines a cosine function to fit and its parameters
"""
import numpy as np
from fitcurve import CurveFit

class FitCosine(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Cosine'
        self.parameterNames = [ 'Frequency','Phase','Contrast','Offset']
        self.parameterValues = [25000.0, 0.0, 1.0, 0.0]
        self.parameterFit = [True,True,True,True]
        
   
    def fitFunc(self, x, p):
        x=x*10**-6     
        evolution = p[2] / 2.0 * np.cos(2.0*np.pi*p[0]*x+p[1]*np.pi) + p[3] + 0.5 
        return evolution