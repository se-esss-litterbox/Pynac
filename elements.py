from collections import namedtuple

Param = namedtuple('Param', ['val', 'unit'])

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
