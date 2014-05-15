"""

This class defines a parabola curve to fit and its parameters

"""
from fitcurve import CurveFit

class FitParabola(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Parabola'
        
        self.parameterNames = ['A', 'B', 'C']
        self.parameterValues = [1.0, 2.0, 3.0]
        self.parameterFit = [True,True,True]

    # idk, something like this?
    def fitFunc(self, x, p):
        """ 
            Parabola
            A*x**2 + B*x + C
            p = [A, B, C]
        """   
        curve = p[0]*x**2 + p[1]*x + p[2]
        return curve