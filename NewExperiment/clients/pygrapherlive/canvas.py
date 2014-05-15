'''
The Canvas Widget handles the actual plotting. 

Because the graph requires the entire dataset to plot, new data received from the
Connections is constantly appended to a copy of the dataset. This data is managed in
a dictionary (dataDict) where they are referenced by the dataset number and directory.
The method, drawPlot, uses the dictionary to determine which dataset to plot. 

The lines are animated onto the canvas via the draw_artist and blit methods. The lines
are stored and managed in a dictionary (plotDict). The dataset number and directory will
reference the data points for the independent variables, the data points for the dependent
variables, and the line objects:

---

Two mechanisms govern how often a plot is drawn. 

1. A main timer cycles constantly updating a counter. When this counter reaches an exact desired number
(such that, for example, 10 counts = 100ms), the plots are drawn. Note: the timer is then stopped in order
to prevent further drawing. Every time the axes change (on_draw()), this counter is reset
back to 0 and the timer is restarted in order to ensure that there is at least a certain amount of time
between repeated calls to draw the plots.

2. New incoming data will automatically redraw the plots. 

---

Because incoming data arrives in pieces, data accumulates in an array inside a dictionary (dataDict). 
Matplotlib uses line objects, stored in plotDict, to draw lines onto the canvas. The line objects use
the data stored in dataDict.

In order to efficiently cap the amount of data stored (and plotted), while maintaining a live stream,
a method involving two arrays of data was employed. The size of the arrays is determined by the global 
variable MAXDATASETSIZE. Initial incoming data is stored in an array of size MAXDATASETSIZE. When the 
data accumulates passed the array's halfway point, a second array is created and a copy of the data is 
stored in a position that is half the MAXDATASETSIZE away from the position in the first array. When the
data reaches the end of the arrays, the data wraps around to the beginning, and the grapher will then switch
which array to plot. Using this method will effectively cap the total number of data and ensure that the 
data being plotted is always in order.

Example:

Initial array:

[0 0 0 0 0 0 0 0 0 0] <- Array being plotted (from position 0 to 0)

Incoming data:

[1 2 3 0 0 0 0 0 0 0] <- Array being plotted (from position 0 to 2)

Passed halfway:

[1 2 3 4 5 6 7 0 0 0] <- Array being plotted (from position 0 to 6)
[6 7 0 0 0 0 0 0 0 0] <- New second array created

Continued:

[1 2 3 4 5 6 7 8 9 0] <- Array being plotted (from position 0 to 8)
[6 7 8 9 0 0 0 0 0 0]

Maximum reached:

    Incoming data: [10, 11, 12, 13]

[11 12 13 4 5 6 7 8 9 10]
[6 7 8 9 10 11 12 13 0 0] <- Array being plotted (from position 0 to 7)

Continued: 

    Incoming data: [14, 15, 16, 17]
    
[11 12 13 14 15 16 17 8 9 10] <- Array being plotted (from position 0 to 6)
[16 17 8 9 10 11 12 13 14 15]

And so on...

Note that sometimes the incoming data has more data points than the array has room for.
This is dealt with by partitioning the incoming data into two pieces such that the first
piece fills the first array, and the second piece starts at beginning of the other array.

---

In order for the above operation to happen successfully, there are certain parameters that
govern its function (stored in plotParametersDict). They are:

1. Data Index
    This number increases constantly with the amount of incoming data. This value modulus 
    MAXDATASETSIZE will give the exact position in the array that data should be added to, 
    and will periodically reset back to zero as this parameter increases.
    
2. Array to Plot
    This number refers to which of the two arrays need be currently plotted.
    
3. Halfway Point (boolean)
    This value indicates whether half of the first array was filled with data. Upon happening,
    the second array will be created.

4. First Pass (boolean)
    This value indicates whether the first array has been entirely filled once. This value
    ensures that the second array is not plotted, because the second array does not contain
    enough data before the first array completely fills up with data.
    
5. Data Initialized (boolean)
    Because the drawPlot is called quickly and repeatedly, this value ensures that no data is 
    drawn until these is actually data to draw.
    
'''

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread
from matplotlib.widgets import RectangleSelector 
from matplotlib import pyplot
from PyQt4 import QtCore
import time
import numpy as np
from itertools import cycle


TIMERREFRESH = .01 #s
MAXDATASETSIZE = 100000
#SCALEFACTOR = 1.5
SCROLLFRACTION = .8; # Data reaches this much of the screen before auto-scroll takes place
AUTOFITSCROLLFRACTION = .65
INDEPENDENT = 0
DEPENDENT = 1
PLOTS = 2
MAX = 1
MIN = 0
FIRST = 0
SECOND = 1
DATAINDEX = 0
ARRAYTOPLOT = 1
HALFWAY = 2
FIRSTPASS = 3
DATAINITIALIZED = 4


class Qt4MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""
    def __init__(self, parent):    
        # instantiate figure
        self.fig = Figure()
        FigureCanvas.__init__(self, self.fig)
        #self.parent = parent
        self.parent = parent      
        self.datasetLabelsDict = {}
        self.plotParametersDict = {}
        self.dataDict = {}
        self.plotDict = {}
        self.maxDatasetSizeReached = False
        self.data = None
        self.drawCounter = 0
        # create plot 
        self.ax = self.fig.add_subplot(111)
        self.ax.grid()
        colormap = pyplot.cm.gist_ncar
#        self.ax.set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, 15)])
        colors = ['b', 'g', 'r', 'm', 'k', colormap(.2), colormap(.9), colormap(.3166), colormap(.7833), colormap(.666)]
        #colors.extend([colormap(i) for i in np.linspace(.2, 0.9, 7)])
        colors.pop(8)
        self.ax.set_color_cycle(colors)
        lines = ["-"]#,"-","-","-","-","-.","-.","-.","-.","-.","--","--","--","--","--",":",":",":",":",":"]
        self.linecycler = cycle(lines)
        self.background = self.copy_from_bbox(self.ax.bbox)
    
    
    # This method is called upon whenever the plot axes change
    def on_draw(self, event):
        self.timer.start(TIMERREFRESH)
        self.drawCounter = 0             
        
    # Initialize a place in the dictionary for the dataset
    def initializeDataset(self, dataset, directory, labels):
        self.dataDict[dataset, directory] = None
        self.datasetLabelsDict[dataset, directory] = labels 
    
    # retrieve and store the new data from Connections
    def setPlotData(self, dataset, directory, data, fit=None):
        # First Time
        numberOfDependentVariables = data.shape[1] - 1 # total number of variables minus the independent variable           
        numberOfDataPoints = data.shape[0]
        if (self.dataDict[dataset, directory] == None):        
            if (directory[-1][-5:len(directory[-1])] != 'Model'): # Check if this is a model
                for i in range(numberOfDependentVariables):
                    label = self.datasetLabelsDict[dataset, directory][i]
                    self.parent.createDatasetCheckbox(dataset, directory, label, i)
#                    self.parent.createDatasetAnalysisCheckbox(dataset, directory, label, i)
#            else:
#                # check if this model already exists!
#                for i in range(self.parent.datasetCheckboxCounter):
#                    if (self.parent.datasetCheckboxListWidget.item(i).text() == str('     ' + str(dataset) + ' - ' + str(directory[-1]) + ' - ' + directory[-1][-5:len(directory[-1])])):
#                        self.parent.datasetCheckboxListWidget.takeItem(i)
#                        print 'taken'
            else:    
                self.parent.createDatasetCheckbox(dataset, directory, directory[-1][-5:len(directory[-1])], 0)

            self.dataDict[dataset, directory] = [[np.zeros([MAXDATASETSIZE]), np.zeros([MAXDATASETSIZE*numberOfDependentVariables]).reshape(numberOfDependentVariables, MAXDATASETSIZE)]]#, [np.zeros([MAXDATASETSIZE]), np.zeros([MAXDATASETSIZE*numberOfDependentVariables]).reshape(numberOfDependentVariables, MAXDATASETSIZE)]]           
            self.plotDict[dataset, directory] = [[]]*numberOfDependentVariables
#            self.parent.createDatasetCheckbox(dataset, directory)
            # plot parameters
            self.plotParametersDict[dataset, directory] = [MAXDATASETSIZE, 0, False, False, False]          
            # update the data points
            self.setPoints(dataset, directory, numberOfDependentVariables, data, numberOfDataPoints, 0)

            self.initializePlots(dataset, directory, numberOfDependentVariables)

            #self.fitData()
            # find initial graph limits
            #self.initialxmin, self.initialxmax = self.getDataXLimits()
            #self.ax.set_xlim(self.initialxmin,self.initialxmax)
            #self.initialymin, self.initialymax = self.getDataYLimits()
            #self.ax.set_ylim(self.initialymin,self.initialymax)
            self.drawLegend()
            self.draw()
            self.timer = QtCore.QTimer()
            QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.constantUpdate)
            self.timer.start(TIMERREFRESH)

            self.cidpress = self.mpl_connect('draw_event', self.on_draw)
            self.drawGraph()
            #if (len(self.dataDict.keys()) == 1) or (fit == True):
            #self.fitData()
        else:
            # New Data      
            
            # dataIndexOffset is dataIndex, offset by MAXDATASETSIZE/2    
            dataIndexOffset = (self.plotParametersDict[dataset, directory][DATAINDEX] + MAXDATASETSIZE/2)%MAXDATASETSIZE
            dataIndex = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
            
            if (self.plotParametersDict[dataset, directory][HALFWAY] == False):
                # if halfway, create the second array
                if (((self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE + numberOfDataPoints) > MAXDATASETSIZE/2)):# and (self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE <= MAXDATASETSIZE/2)):
                    self.plotParametersDict[dataset, directory][HALFWAY] = True
                    self.dataDict[dataset, directory].append([np.zeros([MAXDATASETSIZE]), np.zeros([MAXDATASETSIZE*numberOfDependentVariables]).reshape(numberOfDependentVariables, MAXDATASETSIZE)])
                    self.parseData(dataset, directory, numberOfDependentVariables, data, numberOfDataPoints, dataIndex, dataIndexOffset)       
                else:
                    self.setPoints(dataset, directory, numberOfDependentVariables, data, numberOfDataPoints, dataIndex)
            else:
                self.parseData(dataset, directory, numberOfDependentVariables, data, numberOfDataPoints, dataIndex, dataIndexOffset)               
#                     COME BACK HERE AND FIX INITIALXMIN!!                   
#                    self.initialxmin = self.dataDict[dataset, directory].transpose()[INDEPENDENT][self.plotParametersDict[dataset, directory][DATAINDEX]] # new minimum?                                 
#            if self.parent.datasetCheckboxes[dataset, directory].isChecked():
            self.drawGraph()

#    def switchArray(self, dataset, directory):
#        if (self.plotParametersDict[dataset, directory][ARRAYTOPLOT] == 0):
#            self.plotParametersDict[dataset, directory][ARRAYTOPLOT] = 1
#        else:
#            self.plotParametersDict[dataset, directory][ARRAYTOPLOT] = 0 
#        self.plotParametersDict[dataset, directory][ARRAYTOPLOT] = abs(self.plotParametersDict[dataset, directory][ARRAYTOPLOT] - 1)


    # These conditional statements deal with incoming data that expands outside the array boundaries
    def parseData(self, dataset, directory, numberOfDependentVariables, data, numberOfDataPoints, dataIndex, dataIndexOffset):
        if ((dataIndex + numberOfDataPoints) > MAXDATASETSIZE):
            # split up the data into two pieces
            numberOfDataPoints1 = (MAXDATASETSIZE - dataIndex)
            data1 = data[0:numberOfDataPoints1]
            data2 = data[numberOfDataPoints1:numberOfDataPoints]
            self.setPointsTwoArrays(dataset, directory, numberOfDependentVariables,data1, numberOfDataPoints1, dataIndex, dataIndexOffset)
            # recalculate data indicies
            dataIndex = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
            dataIndexOffset = (self.plotParametersDict[dataset, directory][DATAINDEX] + MAXDATASETSIZE/2)%MAXDATASETSIZE
            numberOfDataPoints2 = numberOfDataPoints - numberOfDataPoints1 
            self.setPointsTwoArrays(dataset, directory, numberOfDependentVariables, data2, numberOfDataPoints2, dataIndex, dataIndexOffset)
        
        elif ((dataIndexOffset + numberOfDataPoints) > MAXDATASETSIZE):
            # split up the data into two pieces
            numberOfDataPoints1 = (MAXDATASETSIZE - dataIndexOffset)
            data1 = data[0:numberOfDataPoints1]
            data2 = data[numberOfDataPoints1:numberOfDataPoints]
            self.setPointsTwoArrays(dataset, directory, numberOfDependentVariables,data1, numberOfDataPoints1, dataIndex, dataIndexOffset)
            # recalculate data indicies           
            dataIndex = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
            dataIndexOffset = (self.plotParametersDict[dataset, directory][DATAINDEX] + MAXDATASETSIZE/2)%MAXDATASETSIZE
            numberOfDataPoints2 = numberOfDataPoints - numberOfDataPoints1 
            self.setPointsTwoArrays(dataset, directory, numberOfDependentVariables,data2, numberOfDataPoints2, dataIndex, dataIndexOffset)            
            #self.plotParametersDict[dataset, directory][FIRSTPASS] = True

        else:
            # This will occur if data is coming at the rate of 1 data point per signal, at most.
            # This might be incorrect (what's written above)
            self.setPointsTwoArrays(dataset, directory, numberOfDependentVariables,data, data.shape[0], dataIndex, dataIndexOffset)
#            print dataIndex, ' ',dataIndexOffset, ' ', numberOfDataPoints

    # Create the initial plot lines
    def initializePlots(self, dataset, directory, numberOfDependentVariables):
        for i in range(numberOfDependentVariables):
            label = self.datasetLabelsDict[dataset, directory][i]
            self.plotDict[dataset, directory][i] = self.ax.plot(self.dataDict[dataset, directory][FIRST][INDEPENDENT],self.dataDict[dataset, directory][FIRST][DEPENDENT][i], label = label,animated=True, linestyle = next(self.linecycler))#'ko', markersize=2
            self.togglePoints(dataset, directory, i)
        self.plotDict[dataset, directory] = self.flatten(self.plotDict[dataset, directory])
        
    
    # This function fills the first array with data (only called for the first half)
    def setPoints(self, dataset, directory, numberOfDependentVariables, data, numberOfDataPoints, dataIndex):
        # update the data points
#        dataIndex = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
        try:
            self.dataDict[dataset, directory][FIRST][INDEPENDENT][self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE:(self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE + numberOfDataPoints)] = data.transpose()[INDEPENDENT]            
            for i in range(numberOfDependentVariables):
                self.dataDict[dataset, directory][FIRST][DEPENDENT][i][dataIndex:(dataIndex + numberOfDataPoints)] = data.transpose()[i+1] # (i + 1) -> in data, the y axes start with the second column
            self.plotParametersDict[dataset, directory][DATAINDEX] = self.plotParametersDict[dataset, directory][DATAINDEX] + numberOfDataPoints
        except ValueError:
            print 'Incoming data size is greater than MAXDATASETSIZE. Consider Increasing MAXDATASETSIZE'
#        if ((dataIndex + numberOfDataPoints) == MAXDATASETSIZE):
#            self.switchArray(dataset, directory)
        
    # This function fills both arrays with data, then updates the data indicies
    def setPointsTwoArrays(self, dataset, directory, numberOfDependentVariables, data, numberOfDataPoints, dataIndex, dataIndexOffset):
        try:
            self.dataDict[dataset, directory][FIRST][INDEPENDENT][dataIndex:(dataIndex + numberOfDataPoints)] = data.transpose()[INDEPENDENT]            
            for i in range(numberOfDependentVariables):
                self.dataDict[dataset, directory][FIRST][DEPENDENT][i][dataIndex:(dataIndex + numberOfDataPoints)] = data.transpose()[i+1] # (i + 1) -> in data, the y axes start with the second column
            self.dataDict[dataset, directory][SECOND][INDEPENDENT][dataIndexOffset:(dataIndexOffset + numberOfDataPoints)] = data.transpose()[INDEPENDENT]            
            for i in range(numberOfDependentVariables):
                self.dataDict[dataset, directory][SECOND][DEPENDENT][i][dataIndexOffset:(dataIndexOffset + numberOfDataPoints)] = data.transpose()[i+1] # (i + 1) -> in data, the y axes start with the second column         
            self.plotParametersDict[dataset, directory][DATAINDEX] = self.plotParametersDict[dataset, directory][DATAINDEX] + numberOfDataPoints
            # If the end of either array is reached
            if ((dataIndex + numberOfDataPoints) == MAXDATASETSIZE):
                self.plotParametersDict[dataset, directory][FIRSTPASS] = True
                # Switch the array to plot
                self.plotParametersDict[dataset, directory][ARRAYTOPLOT] = abs(self.plotParametersDict[dataset, directory][ARRAYTOPLOT] - 1)
            elif ((dataIndexOffset + numberOfDataPoints) == MAXDATASETSIZE):
                if (self.plotParametersDict[dataset, directory][FIRSTPASS] == True):
                    # Switch the array to plot
                    self.plotParametersDict[dataset, directory][ARRAYTOPLOT] = abs(self.plotParametersDict[dataset, directory][ARRAYTOPLOT] - 1)
        except ValueError:
            print 'Incoming data size is greater than MAXDATASETSIZE. Consider Increasing MAXDATASETSIZE'
            
    def constantUpdate(self):
        self.drawCounter = self.drawCounter + 1
        if (self.drawCounter == 10): # 10*10ms = 100ms
            self.timer.stop()
            self.drawGraph()

    def endTimer(self):
        try:
            self.timer.stop()
        except AttributeError:
            pass
       
    # Draw the plot legend
    def drawLegend(self):
#        handles, labels = self.ax.get_legend_handles_labels()
        handles = []
        labels = []
        for dataset,directory, index in self.parent.datasetCheckboxes.keys():
            if self.parent.datasetCheckboxes[dataset, directory, index].isChecked():
                handles.append(self.plotDict[dataset, directory][index])
                labels.append(str(dataset) + ' - ' + self.plotDict[dataset, directory][index].get_label())
        self.ax.legend(handles, labels, loc='best')
    
    # Check which datasets are meant to be plotted and draw them.
    def drawGraph(self):
#        tstartupdate = time.clock()
#        for dataset, directory in self.dataDict:
        for dataset,directory,index in self.parent.datasetCheckboxes.keys():
            # if dataset is intended to be drawn (a checkbox governs this)
            if self.parent.datasetCheckboxes[dataset, directory, index].isChecked():
                self.drawPlot(dataset, directory, index)
#        tstopupdate = time.clock()
#        print tstopupdate - tstartupdate
    
    # plot the data
    def drawPlot(self, dataset, directory, index):#, dataset, directory):
            
        # check if data has been initialized
        try:
            # This first lines tests if the dataInitialized flag exists, otherwise, do not start plotting
            dataInitialized = self.plotParametersDict[dataset, directory][DATAINITIALIZED]          
#            tstartupdate = time.clock()
         
#            numberOfDependentVariables = len(self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][1])
                                              
            # finds the maximum independent variable value
#            self.maxX = self.dataDict[dataset, directory][INDEPENDENT][-1]
#            self.maxX = self.dataDict[dataset, directory][INDEPENDENT][self.plotParametersDict[dataset, directory][DATAINDEX]]
             
            # flatten the data
            self.plotDict[dataset, directory] = self.flatten(self.plotDict[dataset, directory])
            
            # Determine the range of values to plot based on which array needs to be plotted
            if (self.plotParametersDict[dataset, directory][ARRAYTOPLOT] == 0):
                drawRange = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
            else:
                drawRange = (self.plotParametersDict[dataset, directory][DATAINDEX] + MAXDATASETSIZE/2)%MAXDATASETSIZE 
            #print 'drawRange: ', drawRange, ' array to plot: ', self.plotParametersDict[dataset, directory][ARRAYTOPLOT]
            #if the box is checked, otherwise skip this!
            self.plotDict[dataset, directory][index].set_data(self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][INDEPENDENT][0:drawRange],self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][DEPENDENT][index][0:drawRange])
            try:
                self.ax.draw_artist(self.plotDict[dataset, directory][index])
            except AssertionError:
                print 'failed to draw!'
        
            self.blit(self.ax.bbox)
            
            # check to see if the boundary needs updating
            self.updateBoundary(dataset, directory, index, drawRange)
            
#            tstopupdate = time.clock()
#            print tstopupdate - tstartupdate

            # del numberOfDependentVariables
        except:
            pass
    # if the screen has reached the scrollfraction limit, it will update the boundaries
    def updateBoundary(self, dataset, directory, index, drawRange):
        #print 'drawRange: ', drawRange, ' array to plot: ', self.plotParametersDict[dataset, directory][ARRAYTOPLOT]
        #print self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][INDEPENDENT]
        arrayToPlot = self.plotParametersDict[dataset, directory][ARRAYTOPLOT]
        currentX = self.dataDict[dataset, directory][arrayToPlot][INDEPENDENT][drawRange - 1]
        #print currentX
        
        # find the current maximum/minimum Y values between all lines 
        currentYmax = None
        currentYmin = None
        if (currentYmax == None):
            currentYmax = self.dataDict[dataset, directory][arrayToPlot][DEPENDENT][index][drawRange - 1]
            currentYmin = self.dataDict[dataset, directory][arrayToPlot][DEPENDENT][index][drawRange - 1]
        else:
            if (self.dataDict[dataset, directory][arrayToPlot][DEPENDENT][index][-1] > currentYmax):
                currentYmax = self.dataDict[dataset, directory][arrayToPlot][DEPENDENT][index][drawRange - 1]
            elif ((self.dataDict[dataset, directory][arrayToPlot][DEPENDENT][index][-1] < currentYmin)):
                currentYmin = self.dataDict[dataset, directory][arrayToPlot][DEPENDENT][index][drawRange - 1]
        
        xmin, xmax = self.ax.get_xlim()
        xwidth = xmax - xmin
#        print 'xmin, xmax ', xmin, xmax
#        print 'xwidth ', xwidth
        ymin, ymax = self.ax.get_ylim()
        ywidth = ymax - ymin

        # if current x position exceeds certain x coordinate, update the screen
        if self.parent.cb1.isChecked(): 
            if (currentX > SCROLLFRACTION * xwidth + xmin):
                xmin = currentX - xwidth/4
                xmax = xmin + xwidth
                self.ax.set_xlim(xmin, xmax)
                self.draw()
            
        elif self.parent.cb3.isChecked():
            if (currentX > SCROLLFRACTION * xwidth + xmin):
                self.autofitDataX(currentX, MAX)
            elif (currentX < (1 - SCROLLFRACTION- .15) * xwidth + xmin): # -.15 since usually data travels right
                self.autofitDataX(currentX, MIN)        
            if (currentYmax > SCROLLFRACTION * ywidth + ymin):
                self.autofitDataY(currentYmax, MAX)
            elif (currentYmin < (1 - SCROLLFRACTION) * ywidth + ymin):
                self.autofitDataY(currentYmin, MIN)
        
#    def getDataXLimits(self):
#        xmin = None
#        xmax = None
#        for dataset, directory in self.parent.datasetCheckboxes.keys():
#            if (self.plotParametersDict[dataset, directory][ARRAYTOPLOT] == 0):
#                drawRange = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
#            else:
#                drawRange = (self.plotParametersDict[dataset, directory][DATAINDEX] + MAXDATASETSIZE/2)%MAXDATASETSIZE
#            if self.parent.datasetCheckboxes[dataset, directory].isChecked():             
#                for j in range(drawRange):
#                    i = self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][INDEPENDENT][j]
#                    if (xmin == None):
#                        xmin = i
#                        xmax = i
#                    else:
#                        if i < xmin:
#                            xmin = i
#                        elif i > xmax:
#                            xmax = i        
#        return xmin, xmax

    def getDataXLimits(self):
        xmin = None
        xmax = None
        for dataset, directory, index in self.parent.datasetCheckboxes.keys():
            if (self.plotParametersDict[dataset, directory][ARRAYTOPLOT] == 0):
                drawRange = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
            else:
                drawRange = (self.plotParametersDict[dataset, directory][DATAINDEX] + MAXDATASETSIZE/2)%MAXDATASETSIZE
            if self.parent.datasetCheckboxes[dataset, directory, index].isChecked():             
                datasetXmax = self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][INDEPENDENT][0:drawRange].max()
                datasetXmin = self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][INDEPENDENT][0:drawRange].min()
                if (xmin == None):
                    xmin = datasetXmin
                    xmax = datasetXmax
                else:
                    if datasetXmin < xmin:
                        xmin = datasetXmin
                    if datasetXmax > xmax:
                        xmax = datasetXmax
        return xmin, xmax
           
    def getDataYLimits(self):
        ymin = None
        ymax = None
        for dataset, directory, index in self.parent.datasetCheckboxes.keys():
            if (self.plotParametersDict[dataset, directory][ARRAYTOPLOT] == 0):
                drawRange = self.plotParametersDict[dataset, directory][DATAINDEX]%MAXDATASETSIZE
            else:
                drawRange = (self.plotParametersDict[dataset, directory][DATAINDEX] + MAXDATASETSIZE/2)%MAXDATASETSIZE           
            if self.parent.datasetCheckboxes[dataset, directory, index].isChecked():
                datasetYmax = self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][DEPENDENT][index][0:drawRange].max()
                datasetYmin = self.dataDict[dataset, directory][self.plotParametersDict[dataset, directory][ARRAYTOPLOT]][DEPENDENT][index][0:drawRange].min()
                if (ymin == None):
                    ymin = datasetYmin
                    ymax = datasetYmax
                else:
                    if datasetYmin < ymin:
                        ymin = datasetYmin
                    if datasetYmax > ymax:
                        ymax = datasetYmax
        return ymin, ymax

    def autofitDataY(self, currentY, minmax):
        print 'Autofitting in Y'
        ymin, ymax = self.ax.get_ylim()
        dataymin, dataymax = self.getDataYLimits()
        if (minmax == MAX):
            newmaxY = ((1.0/AUTOFITSCROLLFRACTION)*(dataymax - ymin) + ymin)
            self.ax.set_ylim(ymin, newmaxY)
            print 'Y maximum reached, new y limits: ', ymin, newmaxY
        elif (minmax == MIN):
            newminY = (ymax - (1.0/AUTOFITSCROLLFRACTION)*(ymax - dataymin))
            self.ax.set_ylim(newminY, ymax) 
            print 'Y minimum reached, new y limits: ', newminY, ymax
        self.draw()
    
    # update boundaries to fit all the data and leave room for more               
    def autofitDataX(self, currentX, minmax):
        print 'Autofitting in X'
        xmin, xmax = self.ax.get_xlim()
        dataxmin, dataxmax = self.getDataXLimits()
        if (minmax == MAX):
            newmaxX = ((1.0/AUTOFITSCROLLFRACTION)*(dataxmax - xmin) + xmin)
            self.ax.set_xlim(xmin, newmaxX)
            print 'X maximum reached, new x limits: ', xmin, newmaxX
        elif (minmax == MIN):
            newminX = (xmax - (1.0/AUTOFITSCROLLFRACTION)*(xmax - dataxmin))
            self.ax.set_xlim(newminX, xmax)
            print 'X minimum reached, new x limits: ', newminX, xmax
        self.draw()
        
    
    # update boundaries to fit all the data                
    
    def fitData(self):
        xmin, xmax = self.getDataXLimits()
        xwidth = abs(xmax - xmin)
        self.ax.set_xlim(xmin - .1*xwidth, xmax + .1*xwidth)
        ymin, ymax = self.getDataYLimits()
        ywidth = abs(ymax - ymin)
        self.ax.set_ylim(ymin - .1*ywidth, ymax + .1*ywidth)
        self.draw()
        #self.ax.set_xlim(self.initialxmin, self.maxX)
        #self.draw()

    def togglePoints(self, dataset, directory, line):
        pyplot.setp(self.plotDict[dataset, directory][line], linestyle='-', marker='o', markersize=3)
        self.draw()
    
    def toggleLine(self, dataset, directory, line):
        pyplot.setp(self.plotDict[dataset, directory][line], linestyle='-', marker='')
        self.draw()
        
    # to flatten lists (for some reason not built in)
    def flatten(self,l):
            out = []
            for item in l:
                    if isinstance(item, (list, tuple)):
                            out.extend(self.flatten(item))
                    else:
                            out.append(item)
            return out

#
#class HistogramCanvas(FigureCanvas):
#    """Class to plot a histogram"""
#    def __init__(self, parent):    
#        # instantiate figure
#        self.fig = Figure()
#        FigureCanvas.__init__(self, self.fig)
#        self.ax = self.fig.add_subplot(111)
#        self.setupSelector()
#        
#
#    
#    
#    
#    # Initialize a place in the dictionary for the dataset
#    def initializeDataset(self, dataset, directory, labels):
#        self.dataDict[dataset, directory] = None
#        self.datasetLabelsDict[dataset, directory] = labels     
#        
#
#    # retrieve and store the new data from Connections
#    def setPlotData(self, dataset, directory, data):
#        # First Time
#
#        if (self.dataDict[dataset, directory] == None):        
#            pass
#            #do the intial plot stuff
#        else:
#            #update the data, tell it to redraw
#            pass
#
#
#
#    def onselect(self, eclick, erelease):
#        'eclick and erelease are matplotlib events at press and release'
#        print ' startposition : (%f, %f)' % (eclick.xdata, eclick.ydata)
#        print ' endposition   : (%f, %f)' % (erelease.xdata, erelease.ydata)
#          
#        if (eclick.ydata > erelease.ydata):
#            eclick.ydata, erelease.ydata= erelease.ydata, eclick.ydata
#        if (eclick.xdata > erelease.xdata):
#            eclick.xdata, erelease.xdata = erelease.xdata, eclick.xdata
#           
#    def setupSelector(self):
#        self.rectSelect = RectangleSelector(self.ax, self.onselect, drawtype='line', lineprops = dict(color='black', linestyle='-',
#                 linewidth = 2, alpha=0.5))    
#        
#        
#    def constantUpdate(self):
#        self.drawCounter = self.drawCounter + 1
#        if (self.drawCounter == 10): # 10*10ms = 100ms
#            self.timer.stop()
#            self.drawGraph()
#
#    def endTimer(self):
#        try:
#            self.timer.stop()
#        except AttributeError:
#            pass
#
#    # Check which datasets are meant to be plotted and draw them.
#    def drawGraph(self):
##        tstartupdate = time.clock()
#        for dataset, directory in self.dataDict:
#            # if dataset is intended to be drawn (a checkbox governs this)
#            if self.parent.datasetCheckboxes[dataset, directory].isChecked():
#                self.drawPlot(dataset, directory)
