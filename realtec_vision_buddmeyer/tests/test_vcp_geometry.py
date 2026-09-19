# -*- coding: utf-8 -*-
"""Testes de VCPn / VCP_s e heading da rosa 0–360."""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class TestComputeVcpPick:
    def test_offset_matches_mm_scale(self):
        from detection.mask_geometry import compute_vcp_pick

        c = (100.0, 100.0)
        vcp = compute_vcp_pick(c, 0.0, offset_mm=55.0, mm_per_px=1.0, reference=(100.0, 0.0))
        assert abs(_dist(vcp.vcp_n, c) - 55.0) < 1e-6
        assert abs(_dist(vcp.vcp_s, c) - 55.0) < 1e-6
        assert abs(_dist(vcp.vcp_n, vcp.vcp_s) - 110.0) < 1e-6

    def test_vcpn_closer_to_roi_top(self):
        from detection.mask_geometry import compute_vcp_pick

        c = (100.0, 100.0)
        ref = (100.0, 0.0)
        vcp = compute_vcp_pick(c, 90.0, offset_mm=55.0, mm_per_px=1.0, reference=ref)
        assert _dist(vcp.vcp_n, ref) < _dist(vcp.vcp_s, ref)
        assert vcp.vcp_n[1] < c[1]

    def test_heading_north_90(self):
        from detection.mask_geometry import compute_vcp_pick

        vcp = compute_vcp_pick(
            (100.0, 100.0), 90.0, 55.0, 1.0, reference=(100.0, 0.0),
        )
        assert abs(vcp.heading_deg - 90.0) < 1e-6

    def test_heading_south_270(self):
        from detection.mask_geometry import compute_vcp_pick

        vcp = compute_vcp_pick(
            (100.0, 100.0), 90.0, 55.0, 1.0, reference=(100.0, 200.0),
        )
        assert abs(vcp.heading_deg - 270.0) < 1e-6

    def test_heading_east_0(self):
        from detection.mask_geometry import compute_vcp_pick

        vcp = compute_vcp_pick(
            (100.0, 100.0), 0.0, 55.0, 1.0, reference=(200.0, 100.0),
        )
        assert abs(vcp.heading_deg - 0.0) < 1e-6 or abs(vcp.heading_deg - 360.0) < 1e-6

    def test_heading_west_180(self):
        from detection.mask_geometry import compute_vcp_pick

        vcp = compute_vcp_pick(
            (100.0, 100.0), 0.0, 55.0, 1.0, reference=(0.0, 100.0),
        )
        assert abs(vcp.heading_deg - 180.0) < 1e-6

    def test_offset_zero_pick_is_centroid(self):
        from detection.mask_geometry import compute_vcp_pick

        c = (40.0, 80.0)
        vcp = compute_vcp_pick(c, 45.0, offset_mm=0.0, mm_per_px=10.0, reference=(40.0, 0.0))
        assert vcp.vcp_n == c
        assert vcp.vcp_s == c
        assert 0.0 <= vcp.heading_deg < 360.0

    def test_compass_wrap_near_east(self):
        from detection.mask_geometry import compass_heading_deg

        a = compass_heading_deg(1.0, 0.01)
        b = compass_heading_deg(1.0, -0.01)
        assert 0.0 <= a < 10.0 or a > 350.0
        assert b > 350.0 or b < 10.0

    def test_resolve_roi_top_mid(self):
        from detection.mask_geometry import resolve_vcp_reference

        ref = resolve_vcp_reference("roi_top_mid", roi=[10, 20, 80, 40], frame_wh=(200.0, 100.0))
        assert ref == (50.0, 20.0)

    def test_resolve_fov_ignores_roi(self):
        from detection.mask_geometry import resolve_vcp_reference

        ref = resolve_vcp_reference("fov_top_mid", roi=[10, 20, 80, 40], frame_wh=(200.0, 100.0))
        assert ref == (100.0, 0.0)


class TestDetectionSettingsVcp:
    def test_defaults(self):
        from config.settings import DetectionSettings

        cfg = DetectionSettings()
        assert cfg.vcp_offset_mm == 55.0
        assert cfg.vcp_reference == "roi_top_mid"
