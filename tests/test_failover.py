import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import failover_sim


class FailoverTests(unittest.TestCase):
    def test_demo_fails_over_and_back(self):
        report = failover_sim.simulate(failover_sim.demo_samples())
        events = [item["event"] for item in report["transitions"]]
        self.assertEqual(events, ["failover", "failback"])
        self.assertEqual(report["final_active_region"], "primary")

    def test_single_failure_does_not_fail_over(self):
        samples = [
            failover_sim.HealthSample(True, True),
            failover_sim.HealthSample(False, True),
            failover_sim.HealthSample(True, True),
        ]
        report = failover_sim.simulate(samples)
        self.assertEqual(report["transitions"], [])

    def test_unhealthy_secondary_blocks_failover(self):
        samples = [failover_sim.HealthSample(False, False) for _ in range(5)]
        report = failover_sim.simulate(samples)
        self.assertEqual(report["final_active_region"], "primary")

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            failover_sim.FailoverController(0, 3)


if __name__ == "__main__":
    unittest.main()
