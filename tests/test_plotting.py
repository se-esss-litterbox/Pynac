import sys
sys.path.append('../')
import unittest
from Pynac.Plotting import parseEMITGRdata, parseEmitPlot

class parseEMITGRdataTest(unittest.TestCase):
    def test_parseEMITGRdata_basic_operation(self):
        with open('ref_emit.plot', 'r') as f:
            f.readline()
            colData = parseEMITGRdata(f)
            self.assertEqual(len(colData['axisLimsX']), 4)
            self.assertEqual(len(colData['axisLimsY']), 4)
            self.assertEqual(len(colData['axisLimsZ']), 4)
            self.assertGreater(len(colData['horizEllipse']['x']), 0)
            self.assertGreater(len(colData['horizEllipse']['xp']), 0)
            self.assertGreater(len(colData['vertEllipse']['y']), 0)
            self.assertGreater(len(colData['vertEllipse']['yp']), 0)
            self.assertGreater(len(colData['longEllipse']['z']), 0)
            self.assertGreater(len(colData['longEllipse']['zp']), 0)
            dictLength = len(colData['beamDict']['x'])
            self.assertEqual(dictLength, len(colData['beamDict']['xp']))
            self.assertEqual(dictLength, len(colData['beamDict']['y']))
            self.assertEqual(dictLength, len(colData['beamDict']['yp']))
            self.assertEqual(dictLength, len(colData['beamDict']['z']))
            self.assertEqual(dictLength, len(colData['beamDict']['zp']))

class parseEmitPlotTest(unittest.TestCase):
    def test_parseEmitPlot_basic_operation(self):
        parsedData = parseEmitPlot(filename='ref_emit.plot')
        self.assertIsInstance(parsedData[1], list)
        self.assertIsInstance(parsedData[2], list)
        self.assertIsInstance(parsedData[3], list)

        self.assertEqual(parsedData[1][0]['plotTitle'],
                        'PROTON BEAM AT ESS RFQ OUTPUT (62.5 mA)')
        self.assertEqual(parsedData[1][1]['plotTitle'],
                        'BEAM AT OUTPUT HBL Cavities DYNAC-ANA (SCHEFF)')
        self.assertEqual(parsedData[2][0]['plotTitle'],
                        'PROTON BEAM AT ESS RFQ OUTPUT (62.5 mA)')

if __name__ == '__main__':
    unittest.main()
