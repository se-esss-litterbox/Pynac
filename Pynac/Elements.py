'''
Accelerator elements, including methods for their manipulation and conversion to
the representation expected by Dynac.
'''

from Pynac.DataClasses import Param

class Quad:
    '''
    A Pynac representation of a quadrupole magnet.

    Before the simulation is run, any changes made to elements using this class have to
    be put back into the ``lattice`` attribute of `Pynac` using the ``dynacRepresentation``
    method.
    '''
    def __init__(self, L, B, aperRadius):
        self.L = Param(val = L, unit = 'cm')
        self.B = Param(val = B, unit = 'kG')
        self.aperRadius = Param(val = aperRadius, unit = 'cm')

    @classmethod
    def from_dynacRepr(cls, pynacRepr):
        L = float(pynacRepr[1][0][0])
        B = float(pynacRepr[1][0][1])
        aperRadius = float(pynacRepr[1][0][2])
        return cls(L, B, aperRadius)

    def scaleField(self, scalingFactor):
        '''
        Adjust the field of the magnet by the value of ``scalingFactor``.  The adjustment
        is multiplicative, so a value of ``scalingFactor = 1.0`` will result in no change
        of the field.
        '''
        self.B = self.B._replace(val=self.B.val * scalingFactor)

    def dynacRepresentation(self):
        '''
        Return the Dynac representation of this quadrupole instance.
        '''
        return ['QUADRUPO', [[self.L.val, self.B.val, self.aperRadius.val]]]

    def __repr__(self):
        s = 'QUAD:'
        s += ' L = ' + self.L.__repr__()
        s += ' B = ' + self.B.__repr__()
        s += ' aperRadius = ' + self.aperRadius.__repr__()
        return s

class CavityAnalytic:
    '''
    A Pynac representation of a resonant EM cavity (i.e., the ``CAVMC`` model used by Dynac
    to do analytic calculations).

    Before the simulation is run, any changes made to elements using this class have to
    be put back into the ``lattice`` attribute of ``Pynac`` using the ``dynacRepresentation``
    method.
    '''
    def __init__(self, phase, fieldReduction, cavID=0, xesln=0, isec=0):
        self.cavID = Param(val = cavID, unit = None)
        self.xesln = Param(val = xesln, unit = 'cm')
        self.phase = Param(val = phase, unit = 'deg')
        self.fieldReduction = Param(val = fieldReduction, unit = 'percent')
        self.isec = Param(val = isec, unit = None)

    @classmethod
    def from_dynacRepr(cls, pynacRepr):
        cavID = int(pynacRepr[1][0][0])
        xesln = float(pynacRepr[1][1][0])
        phase = float(pynacRepr[1][1][1])
        fieldReduction = float(pynacRepr[1][1][2])
        isec = int(pynacRepr[1][1][3])
        return cls(phase, fieldReduction, cavID, xesln, isec)

    def adjustPhase(self, adjustment):
        '''
        Adjust the accelerating phase of the cavity by the value of ``adjustment``.
        The adjustment is additive, so a value of ``scalingFactor = 0.0`` will result
        in no change of the phase.
        '''
        self.phase = self.phase._replace(val = self.phase.val + adjustment)

    def scaleField(self, scalingFactor):
        '''
        Adjust the accelerating field of the cavity by the value of ``scalingFactor``.
        The adjustment is multiplicative, so a value of ``scalingFactor = 1.0`` will result
        in no change of the field.
        '''
        oldField = self.fieldReduction.val
        newField = 100.0 * (scalingFactor * (1.0 + oldField/100.0) - 1.0)
        self.fieldReduction = self.fieldReduction._replace(val = newField)

    def dynacRepresentation(self):
        '''
        Return the Dynac representation of this cavity instance.
        '''
        return ['CAVMC', [
            [self.cavID.val],
            [self.xesln.val, self.phase.val, self.fieldReduction.val, self.isec.val, 1],
            ]]

class Drift:
    def __init__(self, L):
        self.L = Param(val = L, unit = 'cm')

    @classmethod
    def from_dynacRepr(cls, pynacRepr):
        L = float(pynacRepr[1][0][0])
        return cls(L)

    def dynacRepresentation(self):
        '''
        Return the Dynac representation of this drift instance.
        '''
        return ['DRIFT', [[self.L.val]]]

    def __repr__(self):
        s = 'DRIFT:'
        s += ' L = ' + self.L.__repr__()
        return s

class AccGap:
    def __init__(self, L, TTF, TTFprime, TTFprimeprime, EField, phase, F, atten):
        self.L = Param(val = L, unit = 'cm')
        self.TTF = Param(val = TTF, unit = None)
        self.TTFprime = Param(val = TTFprime, unit = None)
        self.TTFprimeprime = Param(val = TTFprimeprime, unit = None)
        self.EField = Param(val = EField, unit = 'MV/m')
        self.phase = Param(val = phase, unit = 'deg')
        self.F = Param(val = F, unit = 'MHz')
        self.atten = Param(val = atten, unit = None)

        # The following are dummy variables, not used by Dynac
        self.gapID = Param(val = 0, unit = None)
        self.energy = Param(val = 0, unit = 'MeV')
        self.beta = Param(val = 0, unit = None)
        self.S = Param(val = 0, unit = None)
        self.SP = Param(val = 0, unit = None)
        self.quadLength = Param(val = 0, unit = 'cm')
        self.quadStrength = Param(val = 0, unit = 'kG/cm')
        self.accumLen = Param(val = 0, unit = 'cm')

    @classmethod
    def from_dynacRepr(cls, pynacRepr):
        pynacList = pynacRepr[1][0]

        L = float(pynacList[3])
        TTF = float(pynacList[4])
        TTFprime = float(pynacList[5])
        TTFprimeprime = float(pynacList[13])
        EField = float(pynacList[10])
        phase = float(pynacList[11])
        F = float(pynacList[14])
        atten = float(pynacList[15])

        gap = cls(L, TTF, TTFprime, TTFprimeprime, EField, phase, F, atten)
        gap.gapID = Param(val = int(pynacList[0]), unit = None)
        gap.energy = Param(val = float(pynacList[1]), unit = 'MeV')
        gap.beta = Param(val = float(pynacList[2]), unit = None)
        gap.S = Param(val = float(pynacList[6]), unit = None)
        gap.SP = Param(val = float(pynacList[7]), unit = None)
        gap.quadLength = Param(val = float(pynacList[8]), unit = 'cm')
        gap.quadStrength = Param(val = float(pynacList[9]), unit = 'kG/cm')
        gap.accumLen = Param(val = float(pynacList[12]), unit = 'cm')

        return gap

    def dynacRepresentation(self):
        '''
        Return the Dynac representation of this accelerating gap instance.
        '''
        details = [
            self.gapID.val,
            self.energy.val,
            self.beta.val,
            self.L.val,
            self.TTF.val,
            self.TTFprime.val,
            self.S.val,
            self.SP.val,
            self.quadLength.val,
            self.quadStrength.val,
            self.EField.val,
            self.phase.val,
            self.accumLen.val,
            self.TTFprimeprime.val,
            self.F.val,
            self.atten.val,
        ]
        return ['CAVSC', [details]]
