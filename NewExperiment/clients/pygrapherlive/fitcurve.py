"""
The top class that generalizes all curves that can be used to fit to a set of data

ParameterWindow needs to also enumerate stuff rather than be added manually, yikes

"""
from twisted.internet.defer import inlineCallbacks
import numpy as np
from scipy import optimize

# watch out for yields!! don't forget inlinecallbacks!
class CurveFit():
    def __init__(self):
        pass
    
    @inlineCallbacks
    def fitCurve(self, dataset, directory, index, label, parameters, drawCurves):
        params = []
        # data retrieval problem solved
        dataX, dataY = self.getData(dataset, directory, index)
        self.parent.setRanges()
        dataX = np.array(dataX)
#        xmin, xmax = self.parent.parent.parent.qmc.ax.get_xlim()
        xmin = self.parent.minRange.value()
        xmax = self.parent.maxRange.value()
        selectedXValues = np.where((dataX >= xmin) & (dataX <= xmax))[0]
        dataX = dataX[(dataX >= xmin) & (dataX <= xmax)]
        newYData = np.zeros(len(dataX))
        j = 0
        for i in selectedXValues:
            newYData[j] = dataY[i]
            j += 1
        # if no specific parameters are specified, then use the parameter window's
        # change this to self.parent.parameterWindow
        if (parameters == None):
#            height = self.parent.parameterWindow.gaussianHeightDoubleSpinBox.value()
#            center = self.parent.parameterWindow.gaussianCenterDoubleSpinBox.value()
#            sigma =  self.parent.parameterWindow.gaussianSigmaDoubleSpinBox.value()
#            offset = self.parent.parameterWindow.gaussianOffsetDoubleSpinBox.value()
            i=0
            which_to_fit=[]
            for parameterName in self.parent.fitCurveDictionary[self.curveName].parameterNames:
                params.append(self.parent.parameterSpinBoxes[parameterName].value())
                if self.parent.FitParameterBox[parameterName].checkState()==2:
                    which_to_fit.append(i)
                i+=1
        else:
            params = parameters
        
        # use specified parameters
#        else:
#            height = parameters[0]
#            center = parameters[1]
#            sigma =  parameters[2]
#            offset = parameters[3]
            
        # this will actually commense the fitting routine, rather than just drawing using the current parameters
        # this will OVERWRITE the parameters for use (the new parameters are the solutions)
        # smart!
        
        #so basically rather than entering the exact names of the parameters, you should iterate through a list
        # some function should enumerate what these parameters are, in fact, u already do! very nice (parameters[0]..)
        if (drawCurves == False):
              
#            height, center, sigma, offset = self.fit(self.fitFuncGaussian, [height, center, sigma, offset], newYData, dataX)
            solutions = self.fit(self.fitFunc, params, which_to_fit, newYData, dataX)
            
#         self.parent.solutionsDictionary[dataset, directory, label, self.curveName, str(self.parameterNames), index] = solutions
            self.parent.solutionsDictionary[dataset, directory, index, self.curveName] = solutions
            yield self.parent.cxn.data_vault.cd(directory, context = self.parent.context)
            yield self.parent.cxn.data_vault.open(dataset, context = self.parent.context)
#            yield self.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(index)+'-'+'Gaussian', [height, center, sigma, offset], context = self.context)        
            yield self.parent.cxn.data_vault.add_parameter_over_write('Solutions'+'-'+str(index)+'-'+self.curveName, solutions, context = self.parent.context)
        else:
            solutions = params
              
        modelX = np.linspace(dataX[0], dataX[-1], len(dataX)*4)
        # this should be changed to use the fitFunc defined by the user, and NOT the parameter names
#        modelY = self.fitFuncGaussian(modelX, [height, center, sigma, offset])
        modelY = self.fitFunc(modelX, solutions)
        plotData = np.vstack((modelX, modelY)).transpose()
        
        # obviously, instead of Gaussian Model, should just take a string parameter (name)
        directory = list(directory)
        directory[-1] += ' - '
        directory[-1] += label
        directory[-1] += ' - '
        directory[-1] += self.curveName +' Model'
        directory = tuple(directory)
        
        # same name deal here
        self.parent.parent.parent.qmc.initializeDataset(dataset, directory, (label + ' ' + self.curveName +' Model',))
        self.parent.parent.parent.qmc.setPlotData(dataset, directory, plotData)


    def fit(self, function, parameters,fit_these_params, y, x = None):
        def f(params):
            args = []
            j=0
            for i in range(len(parameters)):
                if i not in fit_these_params:
                    args.append(parameters[i])
                else:
                    args.append(params[j])
                    j+=1
            i=0
            for p in args:
                solutions[i] = p
                i+=1
            return (y - function(x, args))
        solutions = [None]*len(parameters)
        if x is None: x = np.arange(y.shape[0])
        print 'Fitting ...',
        optimize.leastsq(f, np.take(parameters,fit_these_params))
        print ' DONE'
        return solutions    
   
    def getData(self, dataset, directory, index):
        dataX, dataY = self.parent.parent.parent.qmc.plotDict[dataset, directory][index].get_data() # dependent variable
        return dataX, dataY
