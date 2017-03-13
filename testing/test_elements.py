import unittest
from Pynac.Core import Pynac
from Pynac import Elements as ele

class ElementTest(unittest.TestCase):
    def setUp(self):
        self.pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_scaleQuad(self):
        quadinds = self.pynacInstance.getXinds('QUADRUPO')
        quad = ele.Quad(self.pynacInstance.lattice[quadinds[0]])
        quad.scaleField(0)
        self.assertEqual(quad.B.val, 0)

    def test_scaleCav(self):
        cavinds = self.pynacInstance.getXinds('CAVMC')
        cav = ele.CavityAnalytic(self.pynacInstance.lattice[cavinds[0]])
        cav.scaleField(0)
        self.assertEqual(cav.fieldReduction.val, -100)

    def test_adjustPhase(self):
        adjustBy = 10
        cavinds = self.pynacInstance.getXinds('CAVMC')
        cav = ele.CavityAnalytic(self.pynacInstance.lattice[cavinds[0]])
        originalPhase = cav.phase
        newPhase = ele.Param(val = originalPhase.val + adjustBy, unit = originalPhase.unit)

        cav.adjustPhase(adjustBy)
        self.assertEqual(cav.phase, newPhase)
        cav.adjustPhase(-adjustBy)
        self.assertEqual(cav.phase, originalPhase)

if __name__ == '__main__':
    unittest.main()
