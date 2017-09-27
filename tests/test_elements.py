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


class ElementInstantiationTests(unittest.TestCase):
    def setUp(self):
        self.pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_quad_class(self):
        quadinds = self.pynacInstance.get_x_inds('QUADRUPO')
        quad = self.pynacInstance.lattice[quadinds[0]]
        self.assertIsInstance(quad, ele.Quad)

    def test_cavmc_class(self):
        cavinds = self.pynacInstance.get_x_inds('CAVMC')
        cav = self.pynacInstance.lattice[cavinds[0]]
        self.assertIsInstance(cav, ele.CavityAnalytic)

    def test_drift_class(self):
        driftinds = self.pynacInstance.get_x_inds('DRIFT')
        drift = self.pynacInstance.lattice[driftinds[0]]
        self.assertIsInstance(drift, ele.Drift)

    def test_cavsc_class(self):
        cavscinds = self.pynacInstance.get_x_inds('CAVSC')
        cav = self.pynacInstance.lattice[cavscinds[0]]
        self.assertIsInstance(cav, ele.AccGap)

    def test_reject_class(self):
        aperinds = self.pynacInstance.get_x_inds('REJECT')
        aper = self.pynacInstance.lattice[aperinds[0]]
        self.assertIsInstance(aper, ele.Set4DAperture)

    def test_buncher_class(self):
        buncherinds = self.pynacInstance.get_x_inds('BUNCHER')
        buncher = self.pynacInstance.lattice[buncherinds[0]]
        self.assertIsInstance(buncher, ele.Buncher)

    def test_field_class(self):
        fieldinds = self.pynacInstance.get_x_inds('FIELD')
        field = self.pynacInstance.lattice[fieldinds[0]]
        self.assertIsInstance(field, ele.AccFieldFromFile)


class ElementManipulationTest(unittest.TestCase):
    def setUp(self):
        self.pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_scaleQuad(self):
        quadinds = self.pynacInstance.get_x_inds('QUADRUPO')
        quad = self.pynacInstance.lattice[quadinds[0]]
        quad.scaleField(0)
        self.assertEqual(quad.B.val, 0)

    def test_scaleCavMC(self):
        cavinds = self.pynacInstance.get_x_inds('CAVMC')
        cav = self.pynacInstance.lattice[cavinds[0]]
        cav.scaleField(0)
        self.assertEqual(cav.fieldReduction.val, -100)

    def test_adjustCAVMCPhase(self):
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
