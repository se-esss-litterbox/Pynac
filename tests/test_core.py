import sys
sys.path.append('../')
import unittest
import os
from Pynac.Core import Pynac, getNumberOfParticles
import Pynac.Elements as pyEle

# class NewPynacLatticeTest(unittest.TestCase):
#     pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))
#
#     def test_conversion2PynacWorks(self):
#         newLattice = []
#         for i in self.pynacInstance.pynacLattice:
#             try:
#                 newLattice.append(i.dynacRepresentation())
#             except AttributeError:
#                 newLattice.append(i)
#         self.assertEqual(self.pynacInstance.lattice, newLattice)

class PynacTest(unittest.TestCase):
    pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_getPlotInds(self):
        self.assertEqual(self.pynacInstance.getNumPlots(), 7)

    def test_RemoveElement(self):
        oldInds = self.pynacInstance.getXinds('DRIFT')
        del self.pynacInstance.lattice[oldInds[0]]
        newInds = self.pynacInstance.getXinds('DRIFT')
        self.assertEqual(len(oldInds), len(newInds) + 1)

    def test_getXinds_quads(self):
        quadInds = self.pynacInstance.getXinds('QUADRUPO')
        self.assertEqual(len(quadInds), 243)

    def test_getXinds_cavmcs(self):
        cavmcinds = self.pynacInstance.getXinds('CAVMC')
        self.assertEqual(len(cavmcinds), 62)

    def test_getXinds_nonsense(self):
        nonsenseinds = self.pynacInstance.getXinds('BLAHBLAHBLAH')
        self.assertEqual(len(nonsenseinds), 0)

class RunningPynacTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))
        self.pynacInstance.run()

    def test_PynacRuns(self):
        self.assertEqual(os.path.exists('dynac.short'), True)

    def test_getNumberOfParticles(self):
        p = getNumberOfParticles()
        self.assertEqual(p, 100)

    @classmethod
    def tearDownClass(self):
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
