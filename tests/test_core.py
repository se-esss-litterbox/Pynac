import sys
sys.path.append('../')
import unittest
import os
from Pynac.Core import Pynac, get_number_of_particles
import Pynac.Elements as pyEle

class PynacTest(unittest.TestCase):
    pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))

    def test_getPlotInds(self):
        self.assertEqual(self.pynacInstance.get_num_plots(), 7)

    def test_RemoveElement(self):
        oldInds = self.pynacInstance.get_x_inds('DRIFT')
        del self.pynacInstance.lattice[oldInds[0]]
        newInds = self.pynacInstance.get_x_inds('DRIFT')
        self.assertEqual(len(oldInds), len(newInds) + 1)

    def test_getXinds_quads(self):
        quadInds = self.pynacInstance.get_x_inds('QUADRUPO')
        self.assertEqual(len(quadInds), 243)

    def test_getXinds_cavmcs(self):
        cavmcinds = self.pynacInstance.get_x_inds('CAVMC')
        self.assertEqual(len(cavmcinds), 62)

    def test_getXinds_nonsense(self):
        nonsenseinds = self.pynacInstance.get_x_inds('BLAHBLAHBLAH')
        self.assertEqual(len(nonsenseinds), 0)

    def test_setNewRDBeamFile(self):
        newfilename = 'testfilename.in'
        self.pynacInstance.set_new_rdbeam_file(newfilename)
        inds = self.pynacInstance.get_x_inds('RDBEAM')
        self.assertEqual(self.pynacInstance.lattice[inds[0]][1][0][0], 'testfilename.in')

class RunningPynacTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.pynacInstance = Pynac(os.path.join(os.path.dirname(__file__), 'ESS_with_SC_ana.in'))
        self.pynacInstance.run()

    def test_PynacRuns(self):
        self.assertTrue(os.path.exists('dynac.short'))

    def test_PynacIsIdenticalToDynac(self):
        with open('emit.plot') as f:
            pynacFile = ''.join(f.readlines())
        with open('ref_emit.plot') as f:
            dynacFile = ''.join(f.readlines())
        self.assertEqual(pynacFile, dynacFile)

    def test_getNumberOfParticles(self):
        p = get_number_of_particles()
        self.assertEqual(p, 1000)

    @classmethod
    def tearDownClass(self):
        # Python3.2 doesn't have FileNotFoundError, so make the following tries to
        # get it, and defaults to OSError if it's not found.
        FileNotFound = getattr(__builtins__,'FileNotFoundError', OSError)

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
            except FileNotFound:
                pass

if __name__ == '__main__':
    unittest.main()
