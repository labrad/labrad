"""
This class defines a Rabi Flop (arbitrary sideband) to fit and its parameters
"""
import numpy as np
from fitcurve import CurveFit
#from labrad import units as U
import timeevolution as te

class FitRabiflop(CurveFit):

    def __init__(self, parent):
        self.parent = parent
        self.curveName = 'Rabi Flop'
        self.parameterNames = ['nbar', 'Rabi Frequency','Delta','Delta Fluctuations','Trap Frequency','Sideband','nmax', 'projection']
        self.parameterValues = [5.0,70000.0,0.0,0.0,2.8,0,1000, np.pi/4]
        self.parameterFit = [True,True,False,False,False,False,False, False]
   
    def fitFunc(self, x, p):
        from labrad import units as U
        flop = te.time_evolution(trap_frequency = U.WithUnit(p[4],'MHz'), projection=p[7], sideband_order = p[5],nmax=p[6])        
        evolution = flop.state_evolution_fluc(x*10**-6,p[0],p[1],p[2],p[3],n_fluc=5.0)
        return evolution