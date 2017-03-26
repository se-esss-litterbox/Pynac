import sys
sys.path.append('../')
import unittest
from Pynac.Plotting import parseEmitPlot

class parseEmitPlotTest(unittest.TestCase):
    def test_parseEmitPlot_basic_operation(self):
        parsedData = parseEmitPlot(filename='ref_emit.plot')
        self.assertIsInstance(parsedData[1], list)
        self.assertIsInstance(parsedData[2], list)
        self.assertIsInstance(parsedData[3], list)

        self.assertEqual(len(parsedData[1]), 2)
        self.assertEqual(len(parsedData[2]), 2)
        self.assertEqual(len(parsedData[3]), 1)

        self.assertEqual(parsedData[1][0]['plotTitle'],
                        'PROTON BEAM AT ESS RFQ OUTPUT (62.5 mA)')
        self.assertEqual(parsedData[1][1]['plotTitle'],
                        'BEAM AT OUTPUT HBL Cavities DYNAC-ANA (SCHEFF)')
        self.assertEqual(parsedData[2][0]['plotTitle'],
                        'PROTON BEAM AT ESS RFQ OUTPUT (62.5 mA)')

if __name__ == '__main__':
    unittest.main()
