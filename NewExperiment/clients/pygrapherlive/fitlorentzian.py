"""

This class defines a Lorentzian curve to fit and its parameters

"""
import numpy as np
from fitcurve import CurveFit
from matplotlib import pylab

class FitLorentzian(CurveFit):

    def __init__(self, parent,ident):
        self.parent = parent
        dataset, directory, index = ident
        dataX, dataY = self.getData(dataset, directory, index)
        Xmax = dataX.max()
        Xmin = dataX.min()
        center = dataX[pylab.unravel_index(np.array(dataY).argmax(),np.array(dataY).shape)]
        FWHM = (Xmax-Xmin)/6.0
        height = dataY.max()
        self.curveName = 'Lorentzian'
        self.parameterNames = ['FWHM', 'Center','Height', 'Offset']
        self.parameterValues = [FWHM,center,height,0.0]
        self.parameterFit = [True,True,True,True]

    # idk, something like this?
    def fitFunc(self, x, p):
        """ 
            Lorentzian
            p = [gamma, center, I, offset]
        
        """  
        p[0] = abs(p[0]) 
        curve = p[3] + p[2]*((p[0]/2)**2/((x - p[1])**2 + (p[0]/2)**2))# Lorentzian
#        curve = p[3] + (1.0/(np.pi*p[0]))*(p[0]/((x - p[1])**2 + p[0]**2))# Lorentzian
        return curve 