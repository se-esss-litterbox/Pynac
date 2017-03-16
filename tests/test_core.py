import sys
sys.path.append('../')
import unittest
import os
from Pynac.Core import Pynac, getNumberOfParticles

class PynacTest(unittest.TestCase):
    def setUp(self):
        self.pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))
        self.pynacInstance._DEBUG = True

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

    def test_PynacRuns(self):
        self.pynacInstance.run()
        self.assertEqual(os.path.exists('dynac.short'), True)

    def test_getNumberOfParticles(self):
        self.pynacInstance.run()
        p = getNumberOfParticles()
        self.assertEqual(p, 1000)

    def tearDown(self):
        filelist = [
            'beam_core.dst',
            'beam_remove.dst',
            'cavdat.out',
            'dynac_in_pr.dst',
            'dynac.dmp',
            'dynac.long',
            'dynac.print',
            'dynac.short',
            'emit.plot',
            'lost_particles.data',
            'pynacrun.log',
        ]
        for f in filelist:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

if __name__ == '__main__':
    unittest.main()
