import sys
sys.path.append('../')
import unittest
from Pynac.Plotting import NewPynPlt

class parseEmitPlotTest(unittest.TestCase):
    def test_parseEmitPlot_basic_operation(self):
        plotter = NewPynPlt(filename='ref_emit.plot')

        self.assertIsInstance(plotter.emitgrColumnData, list)
        self.assertEqual(len(plotter.emitgrColumnData), 2)
        self.assertIn('horizEllipse', plotter.emitgrColumnData[0])
        self.assertIn('vertEllipse', plotter.emitgrColumnData[0])
        self.assertIn('horizEllipse', plotter.emitgrColumnData[0])
        self.assertIn('beam', plotter.emitgrColumnData[0])

        self.assertIsInstance(plotter.profgrColumnData, list)
        self.assertEqual(len(plotter.profgrColumnData), 2)

        self.assertIsInstance(plotter.envelColumnData, list)
        self.assertEqual(len(plotter.envelColumnData), 1)

if __name__ == '__main__':
    unittest.main()
