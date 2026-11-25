#!/usr/bin/env python3
"""Footprints of decorations as the game draws them (F59, agent xeen-fb4-outdoor, 2026-11-25).

A decoration bound to a 3D model (engine/models/decorations.yml, a world's worlds/<world>/models/decorations.yml
replacing an entry of the same name) is drawn `height` high, its GLB scaled to it: its footprint is the model's
horizontal extent at that scale, which decoration_data.txt's collision radius does not say (rock12: radius 16, a
boulder 150 long). A sprite decoration's footprint is its table radius.

  footprint(name) -> (half length, half width) in map units, the longer first; (radius, radius) for a sprite

Used by tools/xeen/town_fit_check.py (`decorations.slope`) and level_generation/projects/xeen/common/wild.py
(`slope_fit`), so the check and the fix measure the same thing.
"""
from __future__ import annotations

import json
import struct
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets_dev'


@lru_cache(maxsize=None)
def _bindings(world: str) -> dict:
    out = {}
    for path in (ASSETS / 'engine' / 'models' / 'decorations.yml', ASSETS / 'worlds' / world / 'models' /
                 'decorations.yml'):
        if path.exists():
            for entry in (yaml.safe_load(path.read_text()) or {}).get('decorations') or []:
                if entry.get('name'):
                    out[str(entry['name']).lower()] = entry
    return out


@lru_cache(maxsize=None)
def _glb_box(model: str):
    path = ASSETS / model
    if not path.exists():
        return None
    data = path.read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    gltf = json.loads(data[20:20 + size])
    lo, hi = [1e18] * 3, [-1e18] * 3
    for mesh in gltf.get('meshes') or []:
        for primitive in mesh.get('primitives') or []:
            accessor = gltf['accessors'][primitive['attributes']['POSITION']]
            if 'min' in accessor and 'max' in accessor:
                lo = [min(a, b) for a, b in zip(lo, accessor['min'])]
                hi = [max(a, b) for a, b in zip(hi, accessor['max'])]
    return (lo, hi) if lo[0] < 1e17 else None


@lru_cache(maxsize=None)
def _table() -> dict:
    sizes = {}
    path = ASSETS / 'engine' / 'data_tables' / 'decoration_data.txt'
    for line in path.read_text(encoding='latin-1').splitlines()[2:]:
        cols = line.split('\t')
        if len(cols) > 5 and cols[1]:
            try:
                sizes[cols[1].lower()] = float(cols[4])
            except ValueError:
                pass
    return sizes


@lru_cache(maxsize=None)
def _descriptions() -> dict:
    out = {}
    path = ASSETS / 'engine' / 'data_tables' / 'decoration_data.txt'
    for line in path.read_text(encoding='latin-1').splitlines()[2:]:
        cols = line.split('\t')
        if len(cols) > 2 and cols[1]:
            out[cols[1].lower()] = cols[2].strip().lower()
    return out


def description(name: str) -> str:
    """decoration_data.txt's description of a decoration ('bones', 'rock', 'cage')."""
    return _descriptions().get(str(name).lower(), '')


def footprint(name: str, world: str = 'xeen') -> tuple[float, float]:
    name = str(name).lower()
    entry = _bindings(world).get(name)
    if entry and entry.get('model') and entry.get('height'):
        box = _glb_box(entry['model'])
        if box is not None:
            lo, hi = box
            tall = hi[1] - lo[1]          # glTF is y-up
            if tall > 1e-6:
                scale = float(entry['height']) / tall
                ex = max(abs(lo[0]), abs(hi[0])) * scale
                ez = max(abs(lo[2]), abs(hi[2])) * scale
                return max(ex, ez), min(ex, ez)
    radius = _table().get(name, 0.0)
    return radius, radius


if __name__ == '__main__':
    import sys
    for arg in sys.argv[1:]:
        print(arg, ['%.0f' % v for v in footprint(arg)])
