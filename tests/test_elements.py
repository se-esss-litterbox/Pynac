import sys
sys.path.append('../')
import unittest
import os
from Pynac.Core import Pynac
from Pynac import Elements as ele


class BasicElementTests(unittest.TestCase):
    def test_pynacelement_is_abstract(self):
        with self.assertRaises(TypeError):
            ele.PynacElement()

    def test_subclassing_pynacelement_improperly(self):
        class SubElement(ele.PynacElement):
            def __init__(self):
                pass
        with self.assertRaises(TypeError):
            SubElement()

    def test_subclassing_pynacelement_properly(self):
        class SubElement(ele.PynacElement):
            def __init__(self):
                pass
            def from_dynacRepr(self, pynacRepr):
                pass
            def dynacRepresentation(self):
                pass
        SubElement()


class ElementManipulationTest(unittest.TestCase):
    pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_scaleQuad(self):
        quadinds = self.pynacInstance.get_x_inds('QUADRUPO')
        quad = self.pynacInstance.lattice[quadinds[0]]
        quad.scaleField(0)
        self.assertEqual(quad.B.val, 0)

    def test_scaleCav(self):
        cavinds = self.pynacInstance.get_x_inds('CAVMC')
        cav = self.pynacInstance.lattice[cavinds[0]]
        cav.scaleField(0)
        self.assertEqual(cav.fieldReduction.val, -100)

    def test_adjustPhase(self):
        adjustBy = 10
        cavinds = self.pynacInstance.get_x_inds('CAVMC')
        cav = self.pynacInstance.lattice[cavinds[0]]
        originalPhase = cav.phase
        newPhase = ele.Param(val = originalPhase.val + adjustBy, unit = originalPhase.unit)

        cav.adjustPhase(adjustBy)
        self.assertEqual(cav.phase, newPhase)
        cav.adjustPhase(-adjustBy)
        self.assertEqual(cav.phase, originalPhase)

if __name__ == '__main__':
    unittest.main()
