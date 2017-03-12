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
from Pynac.Elements import Param

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
        Change the current ``RDBEAM`` command to point at another Dynac input file.
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

SingleDimPS = namedtuple('SingleDimPS', ['pos', 'mom', 'R12', 'normEmit', 'nonNormEmit'])
SingleDimPS.__doc__ = '''
Phase space parameters of the simulated bunch in a single dimension.
'''
SingleDimPS.pos.__doc__ = 'Position spread of the bunch'
SingleDimPS.mom.__doc__ = 'Momentum spread of the bunch'
SingleDimPS.R12.__doc__ = 'R(1,2) of the bunch'
SingleDimPS.normEmit.__doc__ = 'Normalised emittance of the bunch'
SingleDimPS.nonNormEmit.__doc__ = 'Non-normalised emittance of the bunch'

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
