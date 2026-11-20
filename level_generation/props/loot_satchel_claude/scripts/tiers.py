"""Shared tier settings: plan width (m), LOD0 triangle budget, LOD ratios, optional yaw after import."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(ROOT)))
LOD_RATIOS = (0.45, 0.2, 0.08)
TIERS = {
    1: {'width': 0.22, 'lod0': 400, 'colour_from_lod0': True, 'base_projection': True},
    2: {'width': 0.32, 'lod0': 600},
    3: {'width': 0.42, 'lod0': 900},
    4: {'width': 0.52, 'lod0': 1200},
    5: {'width': 0.62, 'lod0': 1500},
    6: {'width': 0.72, 'lod0': 1800, 'gem_emissive': (0.22, 0.03, 0.04)},
}
