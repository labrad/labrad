"""

This class defines a Gaussian curve to fit and its parameters

"""
import numpy as np
from fitcurve import CurveFit

class FitGaussian(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Gaussian'
        self.parameterNames = ['Height', 'Center', 'Sigma', 'Offset']
        self.parameterValues = [1.0, 2.0, 3.0, 4.0]
        self.parameterFit = [True,True,True,True]
    # idk, something like this?
    def fitFunc(self, x, p):
        """ 
            Gaussian
            p = [height, center, sigma, offset]
        
        """   
        curve = p[0]*np.exp(-(((x - p[1])/p[2])**2)/2) + p[3]# gaussian
        return curve    