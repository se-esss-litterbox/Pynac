from collections import namedtuple

Param = namedtuple('Param', ['val', 'unit'])
Param.__doc__ = '''A parameter

val - The parameter's value

unit - The unit the value is given in'''

class Quad:
    def __init__(self, pynacRepr):
        L = pynacRepr[1][0][0]
        B = pynacRepr[1][0][1]
        aperRadius = pynacRepr[1][0][2]
        self.L = Param(val = L, unit = 'cm')
        self.B = Param(val = B, unit = 'kG')
        self.aperRadius = Param(val = aperRadius, unit = 'cm')

    def scaleField(self, scalingFactor):
        self.B = self.B._replace(val=self.B.val * scalingFactor)

    def dynacRepresentation(self):
        return ['QUADRUPO', [[self.L.val, self.B.val, self.aperRadius.val]]]

    def __repr__(self):
        s = 'QUAD:'
        s += ' L = ' + self.L.__repr__()
        s += ' B = ' + self.B.__repr__()
        s += ' aperRadius = ' + self.aperRadius.__repr__()
        return s

class CavityAnalytic:
    def __init__(self, pynacRepr):
        cavID = int(pynacRepr[1][0][0])
        xesln = float(pynacRepr[1][1][0])
        phase = float(pynacRepr[1][1][1])
        fieldReduction = float(pynacRepr[1][1][2])
        isec = int(pynacRepr[1][1][3])
        self.cavID = Param(val = cavID, unit = None)
        self.xesln = Param(val = xesln, unit = 'cm')
        self.phase = Param(val = phase, unit = 'deg')
        self.fieldReduction = Param(val = fieldReduction, unit = 'percent')
        self.isec = Param(val = isec, unit = None)

    def adjustPhase(self, adjustment):
        self.phase = self.phase._replace(val = self.phase.val + adjustment)

    def scaleField(self, scalingFactor):
        oldField = self.fieldReduction.val
        newField = 100.0 * (scalingFactor * (1.0 + oldField/100.0) - 1.0)
        self.fieldReduction = self.fieldReduction._replace(val = newField)

    def dynacRepresentation(self):
        return ['CAVMC', [
            [self.cavID.val],
            [self.xesln.val, self.phase.val, self.fieldReduction.val, self.isec.val, 1],
            ]]
