'''
A collection of classes (mostly named tuples) that are useful for holding data
related to accelerator elements and details of the simulated beam.
'''

from collections import namedtuple
import warnings

Param = namedtuple('Param', ['val', 'unit'])
Param.__repr__ = lambda self: str(self.val) + ' ' + str(self.unit)
try:
    Param.__doc__ = '''
    A representation of a parameter as a value associated with a unit.
    '''
    Param.val.__doc__ = 'The numerical value of the parameter'
    Param.unit.__doc__ = 'The unit used for this parameter'
except AttributeError:
    warnings.warn('Namedtuples cannot have docstrings in this version of Python')

SingleDimPS = namedtuple('SingleDimPS', ['pos', 'mom', 'R12', 'normEmit', 'nonNormEmit'])
try:
    SingleDimPS.__doc__ = '''
    Phase space parameters of the simulated bunch in a single dimension.
    '''
    SingleDimPS.pos.__doc__ = 'Position spread of the bunch'
    SingleDimPS.mom.__doc__ = 'Momentum spread of the bunch'
    SingleDimPS.R12.__doc__ = 'R(1,2) of the bunch'
    SingleDimPS.normEmit.__doc__ = 'Normalised emittance of the bunch'
    SingleDimPS.nonNormEmit.__doc__ = 'Non-normalised emittance of the bunch'
except AttributeError:
    warnings.warn('Namedtuples cannot have docstrings in this version of Python')

CentreOfGravity = namedtuple('CentreOfGravity', ['x', 'xp', 'y', 'yp', 'KE', 'TOF'])
try:
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
except AttributeError:
    warnings.warn('Namedtuples cannot have docstrings in this version of Python')
