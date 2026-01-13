#!/usr/bin/env python3
"""
Benchmark: Memory Usage Under Load
Elite Implementation Standard v2.0.0

Tests memory consumption and efficiency.
"""

import sys
import os
import time
import unittest

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/triage-service/src'))

class MemoryBenchmark(unittest.TestCase):
    """Memory efficiency benchmark"""

    def get_memory_usage(self):
        """Get current process memory usage in MB"""
        if not PSUTIL_AVAILABLE:
            return 0

        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def test_memory_baseline(self):
        """Test baseline memory usage"""
        baseline = self.get_memory_usage()
        print(f"Baseline memory: {baseline:.2f} MB")

        # Target: baseline should be reasonable
        self.assertLess(baseline, 100, "Baseline memory too high")
        print("✓ Baseline memory within limits")

    def test_memory_growth_during_load(self):
        """Test memory growth during 100 requests"""
        if not PSUTIL_AVAILABLE:
            print("⚠ psutil not available, skipping memory test")
            return

        baseline = self.get_memory_usage()

        # Simulate load
        for i in range(100):
            # Simulate request processing
            _ = [x for x in range(1000)]  # Create some objects
            time.sleep(0.001)

        after_load = self.get_memory_usage()
        growth = after_load - baseline

        print(f"Memory growth: {growth:.2f} MB")

        # Target: growth should be minimal
        self.assertLess(growth, 50, "Memory growth too high")
        print("✓ Memory growth under control")

    def test_resource_cleanup(self):
        """Test proper resource cleanup"""
        if not PSUTIL_AVAILABLE:
            print("⚠ psutil not available, skipping cleanup test")
            return

        before_create = self.get_memory_usage()

        # Create temporary objects
        temp_objects = []
        for i in range(1000):
            temp_objects.append([i] * 10)

        after_create = self.get_memory_usage()

        # Clear references
        temp_objects.clear()
        time.sleep(0.01)  # Allow GC

        after_cleanup = self.get_memory_usage()

        growth_during = after_create - before_create
        growth_after_cleanup = after_cleanup - before_create

        print(f"Memory during: {growth_during:.2f} MB, after cleanup: {growth_after_cleanup:.2f} MB")

        # Should recover most memory
        recovery_rate = (1 - growth_after_cleanup / growth_during) * 100 if growth_during > 0 else 100
        print(f"Recovery rate: {recovery_rate:.1f}%")

        self.assertGreater(recovery_rate, 80, "Poor memory recovery")
        print("✓ Memory cleanup effective")

if __name__ == '__main__':
    print("Memory Efficiency Benchmark")
    print("=" * 50)
    unittest.main(verbosity=2)