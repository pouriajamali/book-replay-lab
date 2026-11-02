import unittest
from run_flat_benchmark import reference, summarize, workload

class FlatMeasurementContract(unittest.TestCase):
    def test_workload_count_shape_deterministic(self):
        values=workload(1000,42)
        self.assertEqual(len(values),1000)
        self.assertEqual(values,workload(1000,42))
        self.assertEqual(len(set((s,t) for s,t,q in values[:128])),128)
        self.assertTrue(all(s in (0,1) and 0<=t<64 and 0<=q<=1000 for s,t,q in values))
    def test_zero_clock_readings_retained_not_clamped(self):
        result=summarize([0,0,100,100,200])
        self.assertEqual(result['p50'],100)
        self.assertEqual(result['p99'],200)
        self.assertEqual(result['zero_observations'],2)
        self.assertIsNone(summarize([0,0,0])['p50'])
        self.assertEqual(summarize([0,0,0])['median_resolution'],'RESOLUTION_LIMITED')
    def test_invalid_clock_observations_fail(self):
        for bad in ([],[-1],[True],[0.5]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):summarize(bad)
    def test_reference_rejects_invalid_event_preserving_top(self):
        # A rejected event still enters the checksum, with accepted=false.
        valid=[(0,0,1),(1,63,2)]
        self.assertNotEqual(reference(valid),reference(valid+[(0,64,100)]))
        self.assertEqual(reference(valid+[(0,64,100)]),reference(valid+[(2,0,100)]))

if __name__=='__main__':unittest.main()
