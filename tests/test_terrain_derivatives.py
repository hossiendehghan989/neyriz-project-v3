from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_terrain_derivatives import terrain_derivatives  # noqa: E402


class TerrainDerivativeTests(unittest.TestCase):
    def test_flat_surface_has_zero_slope_and_roughness(self) -> None:
        derivatives = terrain_derivatives(np.full((7, 7), 1000.0), 30.0)
        self.assertAlmostEqual(float(derivatives["slope_degrees"][3, 3]), 0.0, places=6)
        self.assertTrue(np.isnan(derivatives["aspect_degrees"][3, 3]))
        self.assertAlmostEqual(float(derivatives["roughness_stddev_m_3x3"][3, 3]), 0.0, places=6)
        self.assertGreaterEqual(float(derivatives["hillshade_315az_45alt"][3, 3]), 0.0)
        self.assertLessEqual(float(derivatives["hillshade_315az_45alt"][3, 3]), 255.0)

    def test_eastward_plane_has_expected_slope_and_aspect(self) -> None:
        # One metre rise per one metre east gives a 45-degree slope facing east.
        dem = np.tile(np.arange(7, dtype=float) * 30.0, (7, 1))
        derivatives = terrain_derivatives(dem, 30.0)
        self.assertAlmostEqual(float(derivatives["slope_degrees"][3, 3]), 45.0, places=5)
        self.assertAlmostEqual(float(derivatives["aspect_degrees"][3, 3]), 90.0, places=5)
        self.assertAlmostEqual(float(derivatives["roughness_stddev_m_3x3"][3, 3]), np.sqrt(600.0), places=5)

    def test_nan_nodata_is_preserved(self) -> None:
        dem = np.full((7, 7), 1000.0)
        dem[3, 3] = np.nan
        derivatives = terrain_derivatives(dem, 30.0)
        for values in derivatives.values():
            self.assertTrue(np.isnan(values[3, 3]))


if __name__ == "__main__":
    unittest.main()
