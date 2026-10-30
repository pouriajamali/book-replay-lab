import unittest
from run_benchmark import percentile,stream,summarize

class MeasurementContract(unittest.TestCase):
    def test_small_sample_tail_is_explicit_maximum(self):
        self.assertEqual(percentile(list(range(1,32)),.99),31)
        self.assertEqual(percentile(list(range(1,32)),.5),16)
    def test_invalid_clocks_are_not_zero_measurements(self):
        for bad in [[],[0],[True],[1.5],[-1]]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):percentile(bad,.5)
    def test_dataset_count_sequence_and_reproducibility(self):
        rows=stream(1000,42);self.assertEqual(rows,stream(1000,42));self.assertEqual(len(rows),1000)
        self.assertEqual(rows[0],'S 1 100 5 200 5');self.assertTrue(rows[-1].startswith('U 1000 '))
    def test_null_memory_retains_unknown_and_units(self):
        row={'event_count':1000,'batch_ns':[1000,2000,3000],'peak_resident_bytes':None}
        result=summarize(row,1000,3);self.assertIsNone(result['peak_resident_bytes'])
        self.assertEqual(result['batch_p50_amortized_ns_per_event'],2)
    def test_invalid_memory_and_missing_samples_fail(self):
        for memory in [0,True,-1,1.5]:
            with self.subTest(memory=memory),self.assertRaises(ValueError):summarize({'event_count':1000,'batch_ns':[1,2,3],'peak_resident_bytes':memory},1000,3)
        with self.assertRaises(ValueError):summarize({'event_count':1000,'batch_ns':[1,2],'peak_resident_bytes':None},1000,3)

if __name__=='__main__':unittest.main()
