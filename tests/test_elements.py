import sys
sys.path.append('../')
import unittest
import os
from Pynac.Core import Pynac
from Pynac import Elements as ele

class ElementConversionTest(unittest.TestCase):
    pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_convertDrift(self):
        inds = self.pynacInstance.getXinds('DRIFT')
        for ind in inds:
            newEle = ele.Drift.from_dynacRepr(self.pynacInstance.lattice[ind])
            self.assertEqual(newEle.dynacRepresentation(), self.pynacInstance.lattice[ind])

    def test_convertQUAD(self):
        inds = self.pynacInstance.getXinds('QUADRUPO')
        for ind in inds:
            newEle = ele.Quad.from_dynacRepr(self.pynacInstance.lattice[ind])
            self.assertEqual(newEle.dynacRepresentation(), self.pynacInstance.lattice[ind])

    def test_convertCavityAnalytic(self):
        inds = self.pynacInstance.getXinds('CAVMC')
        for ind in inds:
            newEle = ele.CavityAnalytic.from_dynacRepr(self.pynacInstance.lattice[ind])
            self.assertEqual(newEle.dynacRepresentation(), self.pynacInstance.lattice[ind])

    def test_convertCAVSC(self):
        inds = self.pynacInstance.getXinds('CAVSC')
        for ind in inds:
            newEle = ele.AccGap.from_dynacRepr(self.pynacInstance.lattice[ind])
            self.assertEqual(newEle.dynacRepresentation(), self.pynacInstance.lattice[ind])

    def test_convertREJECT(self):
        inds = self.pynacInstance.getXinds('REJECT')
        for ind in inds:
            newEle = ele.Set4DAperture.from_dynacRepr(self.pynacInstance.lattice[ind])
            self.assertEqual(newEle.dynacRepresentation(), self.pynacInstance.lattice[ind])

    def test_convertBUNCHER(self):
        inds = self.pynacInstance.getXinds('BUNCHER')
        for ind in inds:
            newEle = ele.Buncher.from_dynacRepr(self.pynacInstance.lattice[ind])
            self.assertEqual(newEle.dynacRepresentation(), self.pynacInstance.lattice[ind])

    def test_convertFIELD(self):
        inds = self.pynacInstance.getXinds('FIELD')
        for ind in inds:
            newEle = ele.AccFieldFromFile.from_dynacRepr(self.pynacInstance.lattice[ind])
            self.assertEqual(newEle.dynacRepresentation(), self.pynacInstance.lattice[ind])

class ElementManipulationTest(unittest.TestCase):
    pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_scaleQuad(self):
        quadinds = self.pynacInstance.getXinds('QUADRUPO')
        quad = ele.Quad.from_dynacRepr(self.pynacInstance.lattice[quadinds[0]])
        quad.scaleField(0)
        self.assertEqual(quad.B.val, 0)

    def test_scaleCav(self):
        cavinds = self.pynacInstance.getXinds('CAVMC')
        cav = ele.CavityAnalytic.from_dynacRepr(self.pynacInstance.lattice[cavinds[0]])
        cav.scaleField(0)
        self.assertEqual(cav.fieldReduction.val, -100)

    def test_adjustPhase(self):
        adjustBy = 10
        cavinds = self.pynacInstance.getXinds('CAVMC')
        cav = ele.CavityAnalytic.from_dynacRepr(self.pynacInstance.lattice[cavinds[0]])
        originalPhase = cav.phase
        newPhase = ele.Param(val = originalPhase.val + adjustBy, unit = originalPhase.unit)

        cav.adjustPhase(adjustBy)
        self.assertEqual(cav.phase, newPhase)
        cav.adjustPhase(-adjustBy)
        self.assertEqual(cav.phase, originalPhase)

if __name__ == '__main__':
    unittest.main()
