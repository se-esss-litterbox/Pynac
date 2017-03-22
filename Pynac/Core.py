'''
The main module for Pynac.
'''
import subprocess as subp
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor
import os
import shutil
import glob
from collections import namedtuple
import warnings
from IPython.display import display
import ipywidgets as widgets
from ipywidgets import HBox, VBox
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.io import show, push_notebook
from Pynac.DataClasses import Param, SingleDimPS, CentreOfGravity
import Pynac.Elements as pyEle

def multiProcessPynac(filelist, pynacFunc, numIters = 100, max_workers = 8):
    '''
    Use a ProcessPool from the ``concurrent.futures`` module to execute ``numIters``
    number of instances of ``pynacFunc``.  This function takes advantage of ``doSingleDynacProcess``
    and ``pynacInSubDirectory``.
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
    Execute ``pynacFunc`` in the ``pynacInSubDirectory`` context manager.  See the
    docstring for that context manager to understand the meaning of the ``num`` and
    ``filelist`` inputs.

    The primary purpose of this function is to enable multiprocess use of Pynac via
    the ``multiProcessPynac`` function.
    '''
    with pynacInSubDirectory(num, filelist):
        pynacFunc()

@contextmanager
def pynacInSubDirectory(num, filelist):
    '''
    A context manager to create a new directory, move the files listed in ``filelist``
    to that directory, and change to that directory before handing control back to
    context.  The closing action is to change back to the original directory.

    The directory name is based on the ``num`` input, and if it already exists, it
    will be deleted upon entering the context.

    The primary purpose of this function is to enable multiprocess use of Pynac via
    the ``multiProcessPynac`` function.
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
    _DEBUG = False
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

    def __init__(self, filename=None):
        if filename:
            self.filename = filename
            with open(self.filename, 'r') as file:
                self.rawData = [' '.join(line.split()) for line in file]
                if self._DEBUG:
                    print("rawData:")
                    print(self.rawData)
            self._parse()

    @classmethod
    def from_lattice(cls, name, lattice):
        pyn = cls()
        pyn.name = name
        pyn.lattice = lattice
        return pyn

    def run(self):
        '''
        Run the simulation in the current directory.
        '''
        self._startDynacProc(stdin=subp.PIPE, stdout=subp.PIPE)
        str2write = self.name + '\r\n'
        if self._DEBUG:
            with open('pynacrun.log', 'a') as f:
                f.write(str2write)
        self.dynacProc.stdin.write(str2write.encode()) # The name field
        for pynEle in self.lattice:
            try:
                ele = pynEle.dynacRepresentation()
            except AttributeError:
                ele = pynEle
            str2write = ele[0]
            if self._DEBUG:
                with open('pynacrun.log', 'a') as f:
                    f.write(str2write + '\r\n')
            try:
                self.dynacProc.stdin.write((str2write + '\r\n').encode())
            except IOError:
                break
            for datum in ele[1]:
                str2write = ' '.join([str(i) for i in datum])
                if self._DEBUG:
                    with open('pynacrun.log', 'a') as f:
                        f.write(str2write+'\r\n')
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
        return [i for i,x in enumerate(self.lattice) for y in X if DynacFromEle(x) == y]

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
        Change the current ``RDBEAM`` command to point at another Dynac input file.
        This will raise an IndexError if the lattice doesn't contain an RDBEAM
        command.
        '''
        self.lattice[self.getXinds('RDBEAM')[0]][1][0][0] = filename

    def _startDynacProc(self, stdin, stdout):
        # self.dynacProc = subp.Popen(['dynacv6_0','--pipe'], stdin=stdin, stdout=stdout)
        self.dynacProc = subp.Popen(
            ['dynacv6_0','--pipe'],
            stdin=stdin,
            stdout=stdout,
            stderr=subp.PIPE
        )
        if b'Error' in self.dynacProc.stdout.readline():
            raise RuntimeError('Installed version of Dynac should be upgraded to support the --pipe flag')

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
                if self._DEBUG:
                    print(self.lattice[-1])
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
        self.lattice.append(EleFromPynac([dynacStr, dat]))
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

class PhaseSpace:
    '''
    A representation of the phase space of the simulated bunch read from the
    ``dynac.short`` file.  Each of the phase space parameters is represented as a
    ``elements.Parameter`` namedtuple.

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
    Extract all the phase space information (due to ``EMIT`` commands in the input
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
    Queries the ``dynac.short`` file for the number of particles used in the
    simulation.
    '''
    with open('dynac.short') as f:
        dataStr = ''.join(line for line in f.readlines())
        numOfParts = int(dataStr.split('Simulation with')[1].strip().split()[0])
    return numOfParts

def DynacFromEle(ele):
    try:
        dynStr = ele.dynacRepresentation()[0]
    except AttributeError:
        dynStr = ele[0]
    return dynStr

def EleFromPynac(pynacRepr):
    try:
        constructor = getattr(pyEle, pyEle._dynac2pynac[pynacRepr[0]])
        obj = constructor.from_dynacRepr(pynacRepr)
    except AttributeError:
        obj = pynacRepr
    return obj

def buildABeam():
    betaX = widgets.FloatSlider(
        value=7.5,
        min=0.01,
        max=20.0,
        step=0.01,
        description='betaX:',
        disabled=False,
        continuous_update=False,
    )

    alphaX = widgets.FloatSlider(
        value=0.0,
        min=-5.0,
        max=5.0,
        step=0.01,
        description='alphaX:',
        disabled=False,
        continuous_update=False,
    )

    emitX = widgets.FloatSlider(
        value=0.5,
        min=0.01,
        max=10.0,
        step=0.01,
        description='emitX:',
        disabled=False,
        continuous_update=False,
    )

    betaY = widgets.FloatSlider(
        value=7.5,
        min=0.01,
        max=20.0,
        step=0.01,
        description='betaY:',
        disabled=False,
        continuous_update=False,
    )

    alphaY = widgets.FloatSlider(
        value=0.0,
        min=-5.0,
        max=5.0,
        step=0.01,
        description='alphaY:',
        disabled=False,
        continuous_update=False,
    )

    emitY = widgets.FloatSlider(
        value=0.5,
        min=0.01,
        max=10.0,
        step=0.01,
        description='emitY:',
        disabled=False,
        continuous_update=False,
    )

    betaZ = widgets.FloatSlider(
        value=7.5,
        min=0.01,
        max=20.0,
        step=0.01,
        description='betaZ:',
        disabled=False,
        continuous_update=False,
    )

    alphaZ = widgets.FloatSlider(
        value=0.0,
        min=-5.0,
        max=5.0,
        step=0.01,
        description='alphaZ:',
        disabled=False,
        continuous_update=False,
    )

    emitZ = widgets.FloatSlider(
        value=500,
        min=1.0,
        max=1000.0,
        step=1.0,
        description='emitZ:',
        disabled=False,
        continuous_update=False,
    )

    def getPynacInput():
        beam = ['GEBEAM', [
            [4, 1],
            [352.21e6, 1000],
            [0, 0, 0, 0, 0, 0],
            [alphaX.value, betaX.value, emitX.value],
            [alphaY.value, betaY.value, emitY.value],
            [alphaZ.value, betaZ.value, emitZ.value],
        ]]
        return beam

    def getDynacInput():
        beam = 'GEBEAM\r\n'
        beam += '4 1\r\n'
        beam += '352.21e6 1000\r\n'
        beam += '0 0 0 0 0 0\r\n'
        beam += '%f %f %f\r\n' % (alphaX.value, betaX.value, emitX.value)
        beam += '%f %f %f\r\n' % (alphaY.value, betaY.value, emitY.value)
        beam += '%f %f %f' % (alphaZ.value, betaZ.value, emitZ.value)
        return beam

    cssHeightStr = '150px'
    viewBtn = widgets.Button(description="View Pynac Input")
    pynacViewArea = widgets.Textarea()
    pynacViewArea.layout.height = cssHeightStr
    dynacViewArea = widgets.Textarea()
    dynacViewArea.layout.height = cssHeightStr

    pynacViewArea.value = getPynacInput().__str__()
    dynacViewArea.value = getDynacInput()

    lattice = []
    lattice.append(getPynacInput())
    lattice.append(['INPUT', [[938.27231, 1.0, 1.0], [3.6223537, 0.0]]])
    lattice.append(['REFCOG', [[0]]])
    lattice.append(['EMITGR', [['Generated Beam'], [0, 9], [0.5, 80.0, 0.5, 80.0, 0.5, 0.5, 50.0, 1.0]]])
    lattice.append(['STOP', []])

    test = Pynac.from_lattice("Zero-length lattice for beam generation", lattice)
    test.run()

    with open('emit.plot') as f:
        for i in range(204):
            f.readline()
        numParts = int(f.readline())
        x, xp = [], []
        for i in range(numParts):
            dat = f.readline().split()
            x.append(float(dat[0]))
            xp.append(float(dat[1]))
        f.readline()
        for i in range(202):
            f.readline()
        y, yp = [], []
        for i in range(numParts):
            dat = f.readline().split()
            y.append(float(dat[0]))
            yp.append(float(dat[1]))
        f.readline()
        for i in range(203):
            f.readline()
        z, zp = [], []
        for i in range(numParts):
            dat = f.readline().split()
            z.append(float(dat[0]))
            zp.append(float(dat[1]))

    dataSource = ColumnDataSource(data=dict(x=x, xp=xp, y=y, yp=yp, z=z, zp=zp))

    p0 = figure(plot_height=250, plot_width=296, y_range=(-5, 5), x_range=(-1, 1))
    p0.xaxis.axis_label = 'Horizontal position'
    p0.yaxis.axis_label = 'Horizontal angle'
    p0.circle('x', 'xp', color="#2222aa", alpha=0.5, line_width=2, source=dataSource)

    p1 = figure(plot_height=250, plot_width=296, y_range=(-5, 5), x_range=(-1, 1))
    p1.xaxis.axis_label = 'Vertical position'
    p1.yaxis.axis_label = 'Vertical angle'
    p1.circle('y', 'yp', color="#2222aa", alpha=0.5, line_width=2, source=dataSource, name="foo")

    p2 = figure(plot_height=250, plot_width=296, y_range=(-0.1, 0.1), x_range=(-150, 150))
    p2.xaxis.axis_label = 'Longitudinal phase'
    p2.yaxis.axis_label = 'Longitudinal energy'
    p2.circle('z', 'zp', color="#2222aa", alpha=0.5, line_width=2, source=dataSource, name="foo")

    grid = gridplot([[p0, p1, p2]])
    show(grid, notebook_handle=True)
    push_notebook()

    def on_button_clicked(b):
        pynacViewArea.value = getPynacInput().__str__()
        dynacViewArea.value = getDynacInput()
        lattice[0] = getPynacInput()
        test = Pynac.from_lattice("Zero-length lattice for beam generation", lattice)
        test.run()
        with open('emit.plot') as f:
            for i in range(204):
                f.readline()
            numParts = int(f.readline())
            x, xp = [], []
            for i in range(numParts):
                dat = f.readline().split()
                x.append(float(dat[0]))
                xp.append(float(dat[1]))
            f.readline()
            for i in range(202):
                f.readline()
            y, yp = [], []
            for i in range(numParts):
                dat = f.readline().split()
                y.append(float(dat[0]))
                yp.append(float(dat[1]))
            f.readline()
            for i in range(203):
                f.readline()
            z, zp = [], []
            for i in range(numParts):
                dat = f.readline().split()
                z.append(float(dat[0]))
                zp.append(float(dat[1]))
        dataSource.data['x'] = x
        dataSource.data['xp'] = xp
        dataSource.data['y'] = y
        dataSource.data['yp'] = yp
        dataSource.data['z'] = z
        dataSource.data['zp'] = zp
        push_notebook()

    label_layout = widgets.Layout(width='100%')
    twissXLabel = widgets.Label(value = "Horizontal Twiss", layout = label_layout)
    twissYLabel = widgets.Label(value = "Vertical Twiss", layout = label_layout)
    twissZLabel = widgets.Label(value = "Longitudinal Twiss", layout = label_layout)

    for slider in [betaX, alphaX, emitX, betaY, alphaY, emitY, betaZ, alphaZ, emitZ]:
        slider.observe(on_button_clicked)

    pynacBoxLabel = widgets.Label(value = "Pynac Input", layout = label_layout)
    dynacBoxLabel = widgets.Label(value = "Dynac Input", layout = label_layout)

    controls = VBox([
        HBox([
            VBox([twissXLabel, betaX, alphaX, emitX, pynacBoxLabel, pynacViewArea]),
            VBox([twissYLabel, betaY, alphaY, emitY, dynacBoxLabel, dynacViewArea]),
            VBox([twissZLabel, betaZ, alphaZ, emitZ]),
        ]),
    ])
    display(controls)
