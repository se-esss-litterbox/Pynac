from bokeh.io import push_notebook, show, output_notebook
from bokeh.plotting import figure
from bokeh.layouts import gridplot, column, row
from bokeh.models.sources import ColumnDataSource
from bokeh.models import BoxSelectTool
from collections import defaultdict

class PynPlt(object):
    '''
    The main entry point for production of Dynac-style plots.

    When instantiated, this will parse the ``emit.plot`` file in the current
    directory in preparation for producing the Dynac-style plots.

    Note that this module relies on bokeh functionality.
    '''
    def __init__(self):
        with open('emit.plot', 'r') as file:
            self.rawData = [' '.join(line.split()) for line in file]
        self._genTypedData()

        self.plots = []

        ind = 0

        while ind < len(self.typedData):
            plotType = self._setPlotType(self.typedData[ind])
            ind += 1

            if plotType == 'EMITGR':
                self.plots.append({'type': plotType})
                self.plots[-1]['name'] = self.typedData[ind]
                ind += 1
                for dat in ['x','xp','y','yp','z','zp']:
                    self.plots[-1][dat] = []
                    self.plots[-1]['Ellipse-'+dat] = []

                self.plots[-1]['xscale'] = self.typedData[ind]
                ind += 1
                ind = self._getEMITGRdataChunk(ind, 'x')

                self.plots[-1]['yscale'] = self.typedData[ind]
                ind += 1
                ind = self._getEMITGRdataChunk(ind, 'y')

                self.plots[-1]['xyscale'] = self.typedData[ind]
                ind += 1
                self.plots[-1]['zscale'] = self.typedData[ind]
                ind += 1
                ind = self._getEMITGRdataChunk(ind, 'z')

            elif plotType == 'PROFGR':
                self.plots.append({'type': plotType})
                self.plots[-1]['name'] = self.typedData[ind]
                for dat in ['x','y','z']:
                    self.plots[-1][dat] = []
                    self.plots[-1][dat+'N'] = []
                    self.plots[-1][dat+'Val'] = []
                    self.plots[-1][dat+'pN'] = []
                    self.plots[-1][dat+'pVal'] = []

                ind = self._getScaleNAndData(ind, 'xscale', ['z','x'])
                ind = self._getScaleNAndData(ind, 'yscale', ['z','y'])

                for labels in [['xVal','xN'], ['yVal','yN'], ['zVal','zN'],
                              ['xpVal','xpN'], ['ypVal','ypN'], ['zpVal','zpN']]:
                    ind = self._getNumPtsAndData(ind, labels)

                ind += 1

            elif plotType == 'ENVEL':
                self.plots.append({'type': plotType})
                self.plots[-1]['name'] = self.typedData[ind]
                for dat in ['x','y','W','Phi']:
                    self.plots[-1][dat+'S'] = []
                    self.plots[-1][dat+'RMS'] = []

                ind += 1
                self.plots[-1]['xscale'] = self.typedData[ind]
                ind = self._getNumPtsAndData(ind, ['xS','xRMS'])
                ind = self._getNumPtsAndData(ind, ['yS','yRMS'])

                ind += 1
                # Name, scale, numPts, 2x1 data
                ind += 1
                self.plots[-1]['name2'] = self.typedData[ind]
                ind = self._getScaleNAndData(ind, 'Wscale', ['WS','WRMS'])

                ind += 1
                # Name, scale, numPts, 2x1 data
                ind += 1
                self.plots[-1]['name3'] = self.typedData[ind]
                ind = self._getScaleNAndData(ind, 'Phiscale', ['PhiS','PhiRMS'])

                ind += 1

            else:
                raise ValueError("Unknown plotType")

    def _plot(self, ind):
        plotType = self.plots[ind]['type']
        if plotType == 'EMITGR':
            self._plotEMITGR(ind)
        elif plotType == 'ENVEL':
            self._plotENVEL(ind)
        elif plotType == 'PROFGR':
            self._plotPROFGR(ind)

    def plotit(self):
        '''
        Produce the plots requested in the Dynac input file.  This makes the same
        plots as produced by the Dynac ``plotit`` command.
        '''
        [self._plot(i) for i in range(len(self.plots))]

    def _getScaleNAndData(self, i, scaleStr, datStrs):
        i += 1
        self.plots[-1][scaleStr] = self.typedData[i]
        return self._getNumPtsAndData(i, datStrs)

    def _getNumPtsAndData(self, i, datStrs):
        i += 1
        numPts = self.typedData[i]
        i += 1
        for particle in range(numPts):
            self.plots[-1][datStrs[0]].append(self.typedData[i+particle][0])
            self.plots[-1][datStrs[1]].append(self.typedData[i+particle][1])
        i += particle
        return i

    def _getEMITGRdataChunk(self, ind, plane):
        names = [plane, plane+'p', 'Ellipse-'+plane, 'Ellipse-'+plane+'p']

        while isinstance(self.typedData[ind], list):
            self.plots[-1][names[2]].append(self.typedData[ind][0])
            self.plots[-1][names[3]].append(self.typedData[ind][1])
            ind += 1
        self.plots[-1]['numParticles'] = self.typedData[ind]
        ind += 1
        listLen = len(self.typedData[ind])
        while listLen == 2:
            self.plots[-1][names[0]].append(self.typedData[ind][0])
            self.plots[-1][names[1]].append(self.typedData[ind][1])
            ind += 1
            if ind == len(self.typedData):
                break
            try:
                listLen = len(self.typedData[ind])
            except TypeError:
                break
        return ind

    def _genTypedData(self):
        self.typedData = []
        for line in self.rawData:
            if len(line.split(' ')) == 1:
                self.typedData.append(int(line))
            else:
                try:
                    self.typedData.append([float(i) for i in line.split(' ')])
                except ValueError:
                    self.typedData.append(line)

    def _setPlotType(self, val):
        return {
            1: 'EMITGR',
            2: 'PROFGR',
            3: 'ENVEL'
        }[int(val)]

    def _plotENVEL(self, ind):
        data = self.plots[ind]
        p0 = figure(title=data['name'],
            plot_height=400,
            plot_width=700,
            x_range=data['xscale'][:2],
            y_range=data['xscale'][2:]
           )
        p0.line(data['xS'], data['xRMS'], color='black')
        p0.line(data['yS'], data['yRMS'], color='blue')

        p1 = figure(title=data['name2'],
            plot_height=400,
            plot_width=700,
            x_range=data['Wscale'][:2],
            y_range=data['Wscale'][2:]
           )
        p1.line(data['WS'], data['WRMS'], color='black')

        p2 = figure(title=data['name3'],
            plot_height=400,
            plot_width=700,
            x_range=data['Phiscale'][:2],
            y_range=data['Phiscale'][2:]
           )
        p2.line(data['PhiS'], data['PhiRMS'], color='black')

        show(column(p0,p1,p2))

    def _plotPROFGR(self, ind):
        data = self.plots[ind]
        x, y = data['z'], data['x']
        p0 = figure(title=data['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['xscale'][:2],
            y_range=data['xscale'][2:]
           )
        p0.circle(x, y, color='black', size=1)

        x, y = data['z'], data['y']
        p1 = figure(title=data['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['xscale'][:2],
            y_range=data['xscale'][2:]
           )
        p1.circle(x, y, color='black', size=1)

        p2 = figure(title=data['name'],
                    plot_height=400,
                    plot_width=400
                   )
        p2.line(data['xVal'],data['xN'], color='red')
        p2.line(data['yVal'],data['yN'], color='green')
        p2.line(data['zVal'],data['zN'], color='blue')

        p3 = figure(title=data['name'],
                    plot_height=400,
                    plot_width=350
                   )
        p3.line(data['xpVal'],data['xpN'], color='red')
        p3.line(data['ypVal'],data['ypN'], color='green')
        p3.line(data['zpVal'],data['zpN'], color='blue')

        grid = gridplot([[p0,p1],[p2,p3]])

        show(grid)

    def _plotEMITGR(self, ind):
        data = self.plots[ind]

        x, y = data['x'], data['xp']
        p0 = figure(title=data['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['xscale'][:2],
            y_range=data['xscale'][2:],
            x_axis_label='x Position / cm',
            y_axis_label='x Angle / m.rad'
           )
        p0.line(data['Ellipse-x'], data['Ellipse-xp'], line_width=2)
        p0.circle(x, y, color="black", size=1)

        x, y = data['y'], data['yp']
        p1 = figure(title=data['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['yscale'][:2],
            y_range=data['yscale'][2:],
            x_axis_label='y Position / cm',
            y_axis_label='y Angle / m.rad'
           )
        p1.line(data['Ellipse-y'], data['Ellipse-yp'], line_width=2)
        p1.circle(x, y, color="black", size=1)

        x, y = data['x'], data['y']
        p2 = figure(title=self.plots[ind]['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['xscale'][:2],
            y_range=data['yscale'][:2],
            x_axis_label='x Position / cm',
            y_axis_label='y Position / cm'
           )
        p2.circle(x, y, color="black", size=1)

        x, y = data['z'], data['zp']
        p3 = figure(title=self.plots[ind]['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['zscale'][:2],
            y_range=data['zscale'][2:],
            x_axis_label='Phase / deg',
            y_axis_label='Energy offset / MeV'
           )
        p3.line(data['Ellipse-z'], data['Ellipse-zp'], line_width=2)
        p3.circle(x, y, color="black", size=1)

        grid = gridplot([p0,p1],[p2,p3])

        show(grid)

class NewPynPlt:
    def __init__(self, filename='emit.plot'):
        self.filename = filename
        self.plotHandleDict = defaultdict(list)
        self.emitgrColumnData = []
        self.profgrColumnData = []
        self.envelColumnData = []

        self.parseAndOrganise()

    def parseAndOrganise(self):
        parsedData = self._parseEmitPlot()

        for ind, plotData in enumerate(parsedData[1]):
            hEllipseData = plotData['horizEllipse']
            vEllipseData = plotData['vertEllipse']
            lEllipseData = plotData['longEllipse']
            beamData = plotData['beamDict']
            try:
                self.emitgrColumnData[ind]['plotTitle'] = plotData['plotTitle']
                self.emitgrColumnData[ind]['horizEllipse'].data['x'] = hEllipseData['x']
                self.emitgrColumnData[ind]['horizEllipse'].data['xp'] = hEllipseData['xp']
                self.emitgrColumnData[ind]['vertEllipse'].data['y'] = vEllipseData['y']
                self.emitgrColumnData[ind]['vertEllipse'].data['yp'] = vEllipseData['yp']
                self.emitgrColumnData[ind]['longEllipse'].data['z'] = lEllipseData['z']
                self.emitgrColumnData[ind]['longEllipse'].data['zp'] = lEllipseData['zp']
                self.emitgrColumnData[ind]['beam'].data['x'] = beamData['x']
                self.emitgrColumnData[ind]['beam'].data['xp'] = beamData['xp']
                self.emitgrColumnData[ind]['beam'].data['y'] = beamData['y']
                self.emitgrColumnData[ind]['beam'].data['yp'] = beamData['yp']
                self.emitgrColumnData[ind]['beam'].data['z'] = beamData['z']
                self.emitgrColumnData[ind]['beam'].data['zp'] = beamData['zp']
            except IndexError:
                self.emitgrColumnData.append({
                    'plotTitle': plotData['plotTitle'],
                    'horizEllipse': ColumnDataSource(data=dict(
                        x = hEllipseData['x'],
                        xp = hEllipseData['xp']
                    )),
                    'vertEllipse': ColumnDataSource(data=dict(
                        y = vEllipseData['y'],
                        yp = vEllipseData['yp']
                    )),
                    'longEllipse': ColumnDataSource(data=dict(
                        z = lEllipseData['z'],
                        zp = lEllipseData['zp']
                    )),
                    'beam': ColumnDataSource(data=dict(
                        x = beamData['x'],
                        xp = beamData['xp'],
                        y = beamData['y'],
                        yp = beamData['yp'],
                        z = beamData['z'],
                        zp = beamData['zp'],
                    ))
                })

        for ind, plotData in enumerate(parsedData[2]):
            normedProfs = plotData['normedProfiles']
            try:
                raise IndexError
            except IndexError:
                self.profgrColumnData.append({
                    'beam': ColumnDataSource(data=dict(
                        x = plotData['beamDict']['x'],
                        y = plotData['beamDict']['y'],
                        z = plotData['beamDict']['z'],
                    )),
                    'normedProfX': ColumnDataSource(data=dict(
                        x = normedProfs['x'],
                        xval = normedProfs['xval'],
                    )),
                    'normedProfY': ColumnDataSource(data=dict(
                        y = normedProfs['y'],
                        yval = normedProfs['yval'],
                    )),
                    'normedProfZ': ColumnDataSource(data=dict(
                        z = normedProfs['z'],
                        zval = normedProfs['zval'],
                    )),
                    'normedProfXP': ColumnDataSource(data=dict(
                        xp = normedProfs['xp'],
                        xpval = normedProfs['xpval'],
                    )),
                    'normedProfYP': ColumnDataSource(data=dict(
                        yp = normedProfs['yp'],
                        ypval = normedProfs['ypval'],
                    )),
                    'normedProfZP': ColumnDataSource(data=dict(
                        zp = normedProfs['zp'],
                        zpval = normedProfs['zpval'],
                    )),
                })

        for ind, plotData in enumerate(parsedData[3]):
            beamEnv = plotData['envelopes']
            try:
                raise IndexError
            except IndexError:
                self.envelColumnData.append({
                    'envelopes': ColumnDataSource(data=dict(
                        s = beamEnv['s'],
                        x = beamEnv['x'],
                        y = beamEnv['y'],
                        w = beamEnv['dW/W'],
                        phase = beamEnv['phi'],
                    ))
                })

    def plotit(self):
        for i in range(len(self.emitgrColumnData)):
            try:
                test = self.plotHandleDict['emitgrHandle'][i]
                self.plotHandleDict['emitgrHandle'][i] = self.plotEMITGR(i)
            except IndexError:
                self.plotHandleDict['emitgrHandle'].append(self.plotEMITGR(i))
        for i in range(len(self.envelColumnData)):
            try:
                test = self.plotHandleDict['envelHandle'][i]
                self.plotHandleDict['envelHandle'][i] = self.plotENVEL(i)
            except IndexError:
                self.plotHandleDict['envelHandle'].append(self.plotENVEL(i))
        for i in range(len(self.profgrColumnData)):
            try:
                test = self.plotHandleDict['profgrHandle'][i]
                self.plotHandleDict['profgrHandle'][i] = self.plotPROFGR(i)
            except IndexError:
                self.plotHandleDict['profgrHandle'].append(self.plotPROFGR(i))

    def plotEMITGR(self, plotInd):
        fig0 = figure(title=self.emitgrColumnData[plotInd]['plotTitle'],
                      plot_height=400, plot_width=400)
        fig0.add_tools(BoxSelectTool())
        fig1 = figure(plot_height=400, plot_width=400)
        fig1.add_tools(BoxSelectTool())
        fig2 = figure(plot_height=400, plot_width=400)
        fig2.add_tools(BoxSelectTool())
        fig3 = figure(plot_height=400, plot_width=400)
        fig3.add_tools(BoxSelectTool())

        fig0.circle('x', 'xp', color="#2222aa", alpha=0.5,
                    line_width=2, source=self.emitgrColumnData[plotInd]['beam'])
        fig0.line('x', 'xp', line_width=2, color='red',
                    source=self.emitgrColumnData[plotInd]['horizEllipse'])
        fig1.circle('y', 'yp', color="#2222aa", alpha=0.5,
                    line_width=2, source=self.emitgrColumnData[plotInd]['beam'])
        fig1.line('y', 'yp', line_width=2, color='red',
                    source=self.emitgrColumnData[plotInd]['vertEllipse'])
        fig2.circle('x', 'y', color="#2222aa", alpha=0.5,
                    line_width=2, source=self.emitgrColumnData[plotInd]['beam'])
        fig3.circle('z', 'zp', color="#2222aa", alpha=0.5,
                    line_width=2, source=self.emitgrColumnData[plotInd]['beam'])
        fig3.line('z', 'zp', line_width=2, color='red',
                    source=self.emitgrColumnData[plotInd]['longEllipse'])

        grid = gridplot([fig0, fig1], [fig2, fig3])

        return show(grid, notebook_handle=True)

    def plotPROFGR(self, plotInd):
        fig0 = figure(plot_height=400, plot_width=400)
        fig0.add_tools(BoxSelectTool())
        fig1 = figure(plot_height=400, plot_width=400)
        fig1.add_tools(BoxSelectTool())
        fig2 = figure(plot_height=400, plot_width=400)
        fig2.add_tools(BoxSelectTool())
        fig3 = figure(plot_height=400, plot_width=400)
        fig3.add_tools(BoxSelectTool())

        fig0.circle('z', 'x', color="#2222aa", alpha=0.5,
            line_width=2, source=self.profgrColumnData[plotInd]['beam'])
        fig1.circle('z', 'y', color="#2222aa", alpha=0.5,
            line_width=2, source=self.profgrColumnData[plotInd]['beam'])
        fig2.line('x', 'xval', color='red', source=self.profgrColumnData[plotInd]['normedProfX'])
        fig2.line('y', 'yval', color='green', source=self.profgrColumnData[plotInd]['normedProfY'])
        fig2.line('z', 'zval', color='blue', source=self.profgrColumnData[plotInd]['normedProfZ'])
        fig3.line('xp', 'xpval', color='red', source=self.profgrColumnData[plotInd]['normedProfXP'])
        fig3.line('yp', 'ypval', color='green', source=self.profgrColumnData[plotInd]['normedProfYP'])
        fig3.line('zp', 'zpval', color='blue', source=self.profgrColumnData[plotInd]['normedProfZP'])

        grid = gridplot([fig0, fig1], [fig2, fig3])

        return show(grid, notebook_handle=True)

    def plotENVEL(self, plotInd):
        fig0 = figure(plot_height=400, plot_width=800)
        fig0.add_tools(BoxSelectTool())
        fig1 = figure(plot_height=400, plot_width=800)
        fig1.add_tools(BoxSelectTool())
        fig2 = figure(plot_height=400, plot_width=800)
        fig0.line('s', 'x', color='blue', line_width=1, source=self.envelColumnData[plotInd]['envelopes'])
        fig0.line('s', 'y', color='green', line_width=1, source=self.envelColumnData[plotInd]['envelopes'])
        fig1.line('s', 'w', color='blue', line_width=1, source=self.envelColumnData[plotInd]['envelopes'])
        fig2.line('s', 'phase', color='blue', line_width=1, source=self.envelColumnData[plotInd]['envelopes'])

        grid = gridplot([fig0], [fig1], [fig2])

        return show(grid, notebook_handle=True)

    def _parseEmitPlot(self):
        plotTypeDefs = {
            1: self._parseEMITGRdata,
            2: self._parsePROFGRdata,
            3: self._parseENVELdata
        }

        plotData = {1: [], 2: [], 3: []}

        with open(self.filename) as self.emitPlotFile:
            for line in iter(self.emitPlotFile.readline, ''):
                plotTypeNum = int(line.strip())
                plotFunc = plotTypeDefs[plotTypeNum]
                plotData[plotTypeNum].append(plotFunc())

        return plotData

    def _parseEMITGRdata(self):
        output = {}
        output['beamDict'] = dict()

        output['plotTitle'] = self.emitPlotFile.readline().strip()
        output['axisLimsX'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]
        output['horizEllipse'] = self._getPairDataFromFile('x', 'xp')

        numParts = int(self.emitPlotFile.readline().strip())
        output['beamDict'].update(self._getPairDataFromFile('x', 'xp', numParts))

        output['axisLimsY'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]
        output['vertEllipse'] = self._getPairDataFromFile('y', 'yp')

        numParts = int(self.emitPlotFile.readline().strip())
        output['beamDict'].update(self._getPairDataFromFile('y', 'yp', numParts))

        # Skip a line
        self.emitPlotFile.readline()
        output['axisLimsZ'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]

        output['longEllipse'] = self._getPairDataFromFile('z', 'zp')

        numParts = int(self.emitPlotFile.readline().strip())
        output['beamDict'].update(self._getPairDataFromFile('z', 'zp', numParts))

        return output

    def _parsePROFGRdata(self):
        output = {}
        output['plotTitle'] = self.emitPlotFile.readline().strip()
        output['axisLimsX'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]

        output['beamDict'] = dict()

        numParts = int(self.emitPlotFile.readline().strip())
        output['beamDict'].update(self._getPairDataFromFile('z', 'x', numParts))

        output['axisLimsY'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]
        numParts = int(self.emitPlotFile.readline().strip())
        output['beamDict'].update(self._getPairDataFromFile('z', 'y', numParts))

        output['normedProfiles'] = dict()
        numPoints = int(self.emitPlotFile.readline().strip())
        output['normedProfiles'].update(self._getPairDataFromFile('x', 'xval', numPoints))
        numPoints = int(self.emitPlotFile.readline().strip())
        output['normedProfiles'].update(self._getPairDataFromFile('y', 'yval', numPoints))
        numPoints = int(self.emitPlotFile.readline().strip())
        output['normedProfiles'].update(self._getPairDataFromFile('z', 'zval', numPoints))
        numPoints = int(self.emitPlotFile.readline().strip())
        output['normedProfiles'].update(self._getPairDataFromFile('xp', 'xpval', numPoints))
        numPoints = int(self.emitPlotFile.readline().strip())
        output['normedProfiles'].update(self._getPairDataFromFile('yp', 'ypval', numPoints))
        numPoints = int(self.emitPlotFile.readline().strip())
        output['normedProfiles'].update(self._getPairDataFromFile('zp', 'zpval', numPoints))

        return output

    def _parseENVELdata(self):
        output = {}
        output['plotTitleTrans'] = self.emitPlotFile.readline().strip()
        output['axisLimsTrans'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]

        output['envelopes'] = dict()
        numPoints = int(self.emitPlotFile.readline().strip())
        output['envelopes'].update(self._getPairDataFromFile('s', 'x', numPoints))
        numPoints = int(self.emitPlotFile.readline().strip())
        output['envelopes'].update(self._getPairDataFromFile('s', 'y', numPoints))

        # Skip a line
        self.emitPlotFile.readline()

        output['plotTitleEnergy'] = self.emitPlotFile.readline().strip()
        output['axisLimsEnergy'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]

        numPoints = int(self.emitPlotFile.readline().strip())
        output['envelopes'].update(self._getPairDataFromFile('s', 'dW/W', numPoints))

        # Skip a line
        self.emitPlotFile.readline()

        output['plotTitlePhase'] = self.emitPlotFile.readline().strip()
        output['axisLimsPhase'] = [float(i) for i in self.emitPlotFile.readline().strip().split()]

        numPoints = int(self.emitPlotFile.readline().strip())
        output['envelopes'].update(self._getPairDataFromFile('s', 'phi', numPoints))

        return output

    def _getPairDataFromFile(self, x1, x2, numLines=201):
        dataDict = {x1: [], x2: []}
        for _ in range(numLines):
            datum = [float(i) for i in self.emitPlotFile.readline().strip().split()]
            dataDict[x1].append(datum[0])
            dataDict[x2].append(datum[1])
        return dataDict
