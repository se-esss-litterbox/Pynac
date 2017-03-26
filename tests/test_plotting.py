import sys
sys.path.append('../')
import unittest
from Pynac.Plotting import parseEMITGRdata

class parseEMITGRdataTest(unittest.TestCase):
    def test_parseEMITGRdata_basic_operation(self):
        with open('ref_emit.plot', 'r') as f:
            f.readline()
            colData = parseEMITGRdata(f)
            self.assertGreater(len(colData['horizEllipse'].data['x']), 0)
            self.assertGreater(len(colData['horizEllipse'].data['xp']), 0)
            self.assertEqual(len(colData['axisLimsX']), 4)
            self.assertEqual(len(colData['axisLimsY']), 4)
            self.assertGreater(len(colData['vertEllipse'].data['y']), 0)
            self.assertGreater(len(colData['vertEllipse'].data['yp']), 0)
            self.assertGreater(len(colData['longEllipse'].data['z']), 0)
            self.assertGreater(len(colData['longEllipse'].data['zp']), 0)

if __name__ == '__main__':
    unittest.main()
