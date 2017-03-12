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
            y_range=data['xscale'][2:]
           )
        p0.line(data['Ellipse-x'], data['Ellipse-xp'], line_width=2)
        p0.circle(x, y, color="black", size=1)

        x, y = data['y'], data['yp']
        p1 = figure(title=data['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['yscale'][:2],
            y_range=data['yscale'][2:]
           )
        p1.line(data['Ellipse-y'], data['Ellipse-yp'], line_width=2)
        p1.circle(x, y, color="black", size=1)

        x, y = data['x'], data['y']
        p2 = figure(title=self.plots[ind]['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['xscale'][:2],
            y_range=data['yscale'][:2]
           )
        p2.circle(x, y, color="black", size=1)

        x, y = data['z'], data['zp']
        p3 = figure(title=self.plots[ind]['name'],
            plot_height=400,
            plot_width=350,
            x_range=data['zscale'][:2],
            y_range=data['zscale'][2:]
           )
        p3.line(data['Ellipse-z'], data['Ellipse-zp'], line_width=2)
        p3.circle(x, y, color="black", size=1)

        grid = gridplot([p0,p1],[p2,p3])

        show(grid)
