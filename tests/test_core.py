import unittest
import os
from Pynac.Core import Pynac, getNumberOfParticles

class PynacTest(unittest.TestCase):
    def setUp(self):
        self.pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_getPlotInds(self):
        self.assertEqual(self.pynacInstance.getNumPlots(), 7)

    def test_RemoveElement(self):
        plotInds = self.pynacInstance.getPlotInds()
        del self.pynacInstance.lattice[plotInds[0]]
        self.assertEqual(self.pynacInstance.getNumPlots(), 6)

    def test_getXinds_quads(self):
        quadInds = self.pynacInstance.getXinds('QUADRUPO')
        self.assertEqual(len(quadInds), 285)

    def test_getXinds_cavmcs(self):
        cavmcinds = self.pynacInstance.getXinds('CAVMC')
        self.assertEqual(len(cavmcinds), 146)

    def test_getXinds_nonsense(self):
        nonsenseinds = self.pynacInstance.getXinds('BLAHBLAHBLAH')
        self.assertEqual(len(nonsenseinds), 0)

if __name__ == '__main__':
    unittest.main()
