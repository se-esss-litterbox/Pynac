'''
The main module for Pynac.
'''
import subprocess as subp
from contextlib import contextmanager
from bokeh.io import push_notebook, show, output_notebook
from bokeh.plotting import figure
from bokeh.layouts import gridplot, column, row
from concurrent.futures import ProcessPoolExecutor
import os
import shutil
import glob
from collections import namedtuple
from elements import Param

def multiProcessPynac(filelist, pynacFunc, numIters = 100, max_workers = 8):
    '''
    Use a ProcessPool from the `concurrent.futures` module to execute `numIters`
    number of instances of `pynacFunc`.  This function takes advantage of `doSingleDynacProcess`
    and `pynacInSubDirectory`.
    '''
    with ProcessPoolExecutor(max_workers = max_workers) as executor:
        tasks = [executor.submit(doSingleDynacProcess, num, filelist, pynacFunc) for num in range(numIters)]
    exc = [task.exception() for task in tasks if task.exception()]
    if exc:
        return exc
    else:
        return "No errors encountered"

def doSingleDynacProcess(num, filelist, pynacFunc):
    '''
    Execute `pynacFunc` in the `pynacInSubDirectory` context manager.  See the
    docstring for that context manager to understand the meaning of the `num` and
    `filelist` inputs.

    The primary purpose of this function is to enable multiprocess use of Pynac via
    the `multiProcessPynac` function.
    '''
    with pynacInSubDirectory(num, filelist):
        pynacFunc()

@contextmanager
def pynacInSubDirectory(num, filelist):
    '''
    A context manager to create a new directory, move the files listed in `filelist`
    to that directory, and change to that directory before handing control back to
    context.  The closing action is to change back to the original directory.

    The directory name is based on the `num` input, and if it already exists, it
    will be deleted upon entering the context.

    The primary purpose of this function is to enable multiprocess use of Pynac via
    the `multiProcessPynac` function.
    '''
    print('Running %d' % num)
    newDir = 'dynacProc_%04d' % num
    if os.path.isdir(newDir):
        shutil.rmtree(newDir)
    os.mkdir(newDir)
    for f in filelist:
        shutil.copy(f, newDir)
    os.chdir(newDir)

    yield

    os.chdir('..')

class Pynac(object):
    '''
    The primary entry point for performing simulations.  Objects of this class
    contain all the necessary information to perform a Dynac simulation, as well
    as methods to manipulate the lattice, and to make the call to Dynac.

    '''
    _fieldData = {
        'INPUT': 2,
        'RDBEAM': 5,
        'BMAGNET': 4,
        'FSOLE': 2,
        'SECORD': 0,
        'RASYN': 0,
        'EDFLEC': 2,
        'FIRORD': 0,
        'CAVMC': 2,
        'CAVNUM': 2,
        'FIELD': 2,
        'RWFIELD': 0,
        'HARM': 3,
        'EGUN': 2,
        'RFQPTQ': 3,
        'TILT': 2,
        'RANDALI': 2,
        'WRBEAM': 2,
        'EMIT': 0,
        'EMITGR': 3,
        'ENVEL': 4,
        'PROFGR': 3,
        'STOP': 0,
        'ZONES': 2,
        'T3D': 0
    }

    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, 'r') as file:
            self.rawData = [' '.join(line.split()) for line in file]
        self._parse()

    def run(self):
        '''
        Run the simulation in the current directory.
        '''
        self._startDynacProc(stdin=subp.PIPE, stdout=subp.PIPE)
        str2write = self.name + '\r\n'
        self.dynacProc.stdin.write(str2write.encode()) # The name field
        for ele in self.lattice:
            str2write = ele[0]
            try:
                self.dynacProc.stdin.write((ele[0] + '\r\n').encode())
            except IOError:
                break
            for datum in ele[1]:
                str2write = ' '.join([str(i) for i in datum])
                try:
                    self.dynacProc.stdin.write((str2write+'\r\n').encode())
                except IOError:
                    break
        self.dynacProc.stdin.close()
        if self.dynacProc.wait() != 0:
            raise RuntimeError("Errors occured during execution of Dynac")

    def getXinds(self, *X):
        '''
        Return the indices into the lattice list attribute of elements whose Dynac
        type matches the input string.  Multiple input strings can be given, either
        as a comma-separated list or as a genuine Python list.
        '''
        return [i for i,x in enumerate(self.lattice) for y in X if x[0] == y]

    def getPlotInds(self):
        '''
        Return the indices into the lattice list attribute of elements that result
        in Dynac plot output.
        '''
        return self.getXinds('EMITGR','ENVEL','PROFGR')

    def getNumPlots(self):
        '''
        Return the number of Dynac plots that will be output when Dynac is run.
        '''
        return len(self.getPlotInds()) + 2 * len(self.getXinds('ENVEL'))

    def setNewRDBEAMfile(self, filename):
        '''
        Change the current 'RDBEAM' command to point at another Dynac input file.
        This will raise an IndexError if the lattice doesn't contain an RDBEAM
        command.
        '''
        self.lattice[self.getXinds('RDBEAM')[0]][1][0][0] = filename

    def _startDynacProc(self, stdin, stdout):
        self.dynacProc = subp.Popen(['dynacv6_0','--pipe'], stdin=stdin, stdout=stdout)

    def _loop(self, item):
        print(item)
        self.dynacProc.stdin.write(item[0] + '\r\n')
        for data in item[1]:
            self.dynacProc.stdin.write(data)

    def _parse(self):
        self.lattice = []
        self.name = self.rawData[0]

        ind = 1
        while ind < len(self.rawData):
            if not (self.rawData[ind] == '' or self.rawData[ind][0] == ';'):
                ind = self._parsedChunk(ind)
            ind += 1

    def _parsedChunk(self, currentInd):
        dynacStr = self.rawData[currentInd]
        try:
            numFields = self._fieldData[dynacStr]
        except KeyError:
            if dynacStr == 'GEBEAM':
                numFields = self._getNumFieldsFromiTwiss(currentInd)
            elif dynacStr == 'SCDYNAC':
                numFields = self._getNumFieldsFromISCSP(currentInd)
            else:
                numFields = 1
        dataStr = [self.rawData[currentInd+i+1] for i in range(numFields)]
        dat = []
        for term in dataStr:
            try:
                if self._mightBeNumber(term):
                    dat.append([float(term)])
                else:
                    dat.append([int(term)])
            except ValueError:
                try:
                    dat.append([float(i) if self._mightBeNumber(i) else int(i) for i in term.split(' ')])
                except ValueError:
                    dat.append([term])
        self.lattice.append([dynacStr, dat])
        return currentInd + numFields

    def _getNumFieldsFromiTwiss(self, ind):
        iTwiss = self.rawData[ind+1].split()[1]
        return {'1': 6, '0': 4}[iTwiss]

    def _getNumFieldsFromISCSP(self, ind):
        iscsp = self.rawData[ind+1]
        return {
            '1': 3,
            '-1': 6,
            '2': 3,
            '3': 3 if self.rawData[ind+3]=='0' else 4
        }[iscsp]

    def _mightBeNumber(self, thing):
        return ('.' in thing) or ('e' in thing) or ('E' in thing)

class PynPlt(object):
    '''
    The main entry point for production of Dynac-style plots.

    When instantiated, this will parse the `emit.plot` file in the current
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
        plots as produced by the Dynac `plotit` command.
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
            plot_width=900,
            x_range=data['xscale'][:2],
            y_range=data['xscale'][2:]
           )
        p0.line(data['xS'], data['xRMS'], color='black')
        p0.line(data['yS'], data['yRMS'], color='blue')

        p1 = figure(title=data['name2'],
            plot_height=400,
            plot_width=900,
            x_range=data['Wscale'][:2],
            y_range=data['Wscale'][2:]
           )
        p1.line(data['WS'], data['WRMS'], color='black')

        p2 = figure(title=data['name3'],
            plot_height=400,
            plot_width=900,
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
            plot_width=400,
            x_range=data['xscale'][:2],
            y_range=data['xscale'][2:]
           )
        p0.circle(x, y, color='black', size=1)

        x, y = data['z'], data['y']
        p1 = figure(title=data['name'],
            plot_height=400,
            plot_width=400,
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
                    plot_width=400
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
            plot_width=400,
            x_range=data['xscale'][:2],
            y_range=data['xscale'][2:]
           )
        p0.line(data['Ellipse-x'], data['Ellipse-xp'], line_width=2)
        p0.circle(x, y, color="black", size=1)

        x, y = data['y'], data['yp']
        p1 = figure(title=data['name'],
            plot_height=400,
            plot_width=400,
            x_range=data['yscale'][:2],
            y_range=data['yscale'][2:]
           )
        p1.line(data['Ellipse-y'], data['Ellipse-yp'], line_width=2)
        p1.circle(x, y, color="black", size=1)

        x, y = data['x'], data['y']
        p2 = figure(title=self.plots[ind]['name'],
            plot_height=400,
            plot_width=400,
            x_range=data['xscale'][:2],
            y_range=data['yscale'][:2]
           )
        p2.circle(x, y, color="black", size=1)

        x, y = data['z'], data['zp']
        p3 = figure(title=self.plots[ind]['name'],
            plot_height=400,
            plot_width=400,
            x_range=data['zscale'][:2],
            y_range=data['zscale'][2:]
           )
        p3.line(data['Ellipse-z'], data['Ellipse-zp'], line_width=2)
        p3.circle(x, y, color="black", size=1)

        grid = gridplot([p0,p1],[p2,p3])

        show(grid)

SingleDimPS = namedtuple('SingleDimPS', ['pos', 'mom', 'R12', 'normEmit', 'nonNormEmit'])


CentreOfGravity = namedtuple('CentreOfGravity', ['x', 'xp', 'y', 'yp', 'KE', 'TOF'])
CentreOfGravity.__doc__ = '''
6D centre of gravity of the simulated bunch.  Each of the following is of type
elements.Parameter.
'''
CentreOfGravity.x.__doc__ = 'Horizontal location parameter'
CentreOfGravity.xp.__doc__ = 'Horizontal momentum parameter'
CentreOfGravity.y.__doc__ = 'Vertical location parameter'
CentreOfGravity.yp.__doc__ = 'Vertical momentum parameter'
CentreOfGravity.KE.__doc__ = 'Kinetic energy parameter'
CentreOfGravity.TOF.__doc__ = 'Time-of-flight parameter'

class PhaseSpace:
    '''
    A representation of the phase space of the simulated bunch read from the
    `dynac.short` file.  Each of the phase space parameters is represented as a
    `elements.Parameter` namedtuple.

    This class is intended to be used in interactive explorations of the data
    produced during Pynac simulations.
    '''
    def __init__(self, dataStrMatrix):
        self.dataStrMatrix = dataStrMatrix
        self.xPhaseSpace = self._getPSFromLine(5)
        self.yPhaseSpace = self._getPSFromLine(6)
        self.zPhaseSpace = self._getPSFromLine(4)
        self.COG = CentreOfGravity(
            x = Param(val = float(self.dataStrMatrix[1][0]), unit = 'mm'),
            xp = Param(val = float(self.dataStrMatrix[1][1]), unit = 'mrad'),
            y = Param(val = float(self.dataStrMatrix[1][2]), unit = 'mm'),
            yp = Param(val = float(self.dataStrMatrix[1][3]), unit = 'mrad'),
            KE = Param(val = float(self.dataStrMatrix[0][3]), unit = 'MeV'),
            TOF = Param(val = float(self.dataStrMatrix[0][4]), unit = 'deg'),
        )
        self.particlesLeft = Param(val = float(self.dataStrMatrix[4][5]), unit = 'num')

    def _getPSFromLine(self, num):
        try:
            test = float(self.dataStrMatrix[num][6])
            return SingleDimPS(
                pos = Param(val = float(self.dataStrMatrix[num][0]), unit = 'mm'),
                mom = Param(val = float(self.dataStrMatrix[num][1]), unit = 'mrad'),
                R12 = Param(val = float(self.dataStrMatrix[num][2]), unit = '?'),
                normEmit = Param(val = float(self.dataStrMatrix[num][3]), unit = 'mm.mrad'),
                nonNormEmit = Param(val = float(self.dataStrMatrix[num][6]), unit = 'mm.mrad'),
            )
        except:
            return SingleDimPS(
                pos = Param(val = float(self.dataStrMatrix[num][0]), unit = 'deg'),
                mom = Param(val = float(self.dataStrMatrix[num][1]), unit = 'keV'),
                R12 = Param(val = float(self.dataStrMatrix[num][2]), unit = '?'),
                normEmit = Param(val = float(self.dataStrMatrix[num][3]), unit = 'keV.ns'),
                nonNormEmit = Param(val = None, unit = None),
            )

    def __repr__(self):
        reprStr = 'COG: ' + self.COG.__repr__()
        reprStr += '\nparticles left: ' + self.particlesLeft.__repr__()
        reprStr += '\nx: ' + self.xPhaseSpace.__repr__()
        reprStr += '\ny: ' + self.yPhaseSpace.__repr__()
        reprStr += '\nz: ' + self.zPhaseSpace.__repr__()
        return reprStr

def makePhaseSpaceList():
    '''
    Extract all the phase space information (due to `EMIT` commands in the input
    file), and create a list of PhaseSpace objects.  The primary purpose of this
    is for interactive explorations of the data produced during Pynac simulations.
    '''
    with open('dynac.short') as f:
        dataStr = ''.join(line for line in f.readlines())
        dataStrArray = dataStr.split('beam (emit card)')[1:]
        dataStrMatrix = [[j.strip().split() for j in i] for i in[chunk.split('\n')[1:8] for chunk in dataStrArray]]

        return [PhaseSpace(data) for data in dataStrMatrix]

def getNumberOfParticles():
    '''
    Queries the `dynac.short` file for the number of particles used in the
    simulation.
    '''
    with open('dynac.short') as f:
        dataStr = ''.join(line for line in f.readlines())
        numOfParts = int(dataStr.split('Simulation with')[1].strip().split()[0])
    return numOfParts
