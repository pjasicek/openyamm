#!/usr/bin/env python3
"""Seat contact of MM9's seated posed figures (M18 of devdocs/mm9_rework/FINAL_REBUILD_WORK.md, 2026-11-06).

The props projects placed every MoveToFloor posed figure with its feet on the surface under its DAT position. Under
the seated townsfolk that surface is not the room floor but MM9's PhysicsBSP blocker over the bench, pew or throne
step (Sturmford's tavern: 19804, 47 units over the floor at 19757), and in The Arena the stand's step they sit on: the
feet stood on the seat and the figures floated a seat height over it. MM9 does not put the feet there: MoveToFloor
puts the bottom of the object's dims box on that surface (pos = hit + dims.y + 0.1 LT), and the seated libraries'
dims (PeasantSeated.abc, PeasantMS2's MP_2s: half height 20 LT, origin -15) end where the thighs are, 19 LT over the
feet. So a seated figure's seat plane (its thighs' underside) belongs on the seat.

Measured here on the installed models, placed the way the engine places them (glTF (x, y, z) -> (-x, z, y), scaled by
binding height over the model's height, turned by the facing, at the entity position plus the binding's z_offset):
- seat plane: the 20th percentile of the figure's underside (lowest sample per 2-unit cell) between 20 % and 60 % of
  its height over its feet (the thighs and seat; the feet, calves and table-resting arms are outside that band);
- seat top: the highest surface of the other placements' models in that seat footprint (radius 5 units) below the
  seat plane + 20, else the figure's floor_z (the MoveToFloor surface: MM9's dims rule, The Arena's steps);
- need: seat top - seat plane - SINK (MM9's dims box bottom lies 2.6 units over the measured thigh underside).

Used by seated_offsets.py (per decoration z_offset in the bindings) and placements.py (the seat-aware z of a figure
whose decoration is shared with a map where it sits right: Bjarni on Sturmford's throne)."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'level_generation/props/mm9_isleofashes_claude/scripts'))
from glbio import array, read_glb  # noqa: E402

BINDING_FILES = (REPO / 'assets_dev/engine/models/indoor_decorations.yml',
                 REPO / 'assets_dev/worlds/mm9/models/indoor_decorations.yml')
SINK = 2.0                # units the seat plane goes under the seat top (MM9's dims box: 2.6)
FOOTPRINT = 5.0           # seat footprint radius, units
NEIGHBOURS = 200.0        # placements considered as seats, units


def bindings():
    """Effective indoor bindings by lowercase name (the world's entries replace the engine's)."""
    out = {}
    for path in BINDING_FILES:
        for entry in (yaml.safe_load(path.read_text()) or {}).get('decorations') or []:
            out[entry['name'].lower()] = entry
    return out


_MODELS = {}


def model_triangles(model):
    """LOD0 triangles of a binding's model (the source GLB) and the full LOD0's height (glTF y, flame cards included:
    the engine's bounds)."""
    if model not in _MODELS:
        path = REPO / 'assets_source' / model
        document, binary = read_glb(path if path.exists() else REPO / 'assets_dev' / model)
        node = next(n for n in document['nodes'] if 'mesh' in n)
        every, solid = [], []
        for p in document['meshes'][node['mesh']]['primitives']:
            tris = array(document, binary, p['attributes']['POSITION']).astype(float)[
                array(document, binary, p['indices'])[:, 0].reshape(-1, 3)]
            every.append(tris)
            if document['materials'][p['material']]['name'] != 'Fire':
                solid.append(tris)
        every = np.concatenate(every)
        _MODELS[model] = (np.concatenate(solid), float(every[..., 1].max() - every[..., 1].min()))
    return _MODELS[model]


def placed_samples(entry, binding, z_offset=None, step=1.5):
    """Surface samples of a placement's model where the engine draws it (z_offset None: the binding's)."""
    tris, height = model_triangles(binding['model'])
    yaw = math.radians(entry.get('yaw_degrees', 0.0) + float(binding.get('yaw_offset', 0.0) or 0.0))
    c, s = math.cos(yaw), math.sin(yaw)
    turn = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    local = np.stack([-tris[..., 0], tris[..., 2], tris[..., 1]], -1) * (float(binding['height']) / height)
    dz = float(binding.get('z_offset', 0.0) or 0.0) if z_offset is None else z_offset
    tris = local @ turn.T + np.array([entry['x'], entry['y'], entry['z'] + dz])
    out = [tris.reshape(-1, 3)]
    for t in tris:
        n = int(max(np.linalg.norm(t[1] - t[0]), np.linalg.norm(t[2] - t[0]), np.linalg.norm(t[2] - t[1])) / step)
        if n < 1:
            continue
        u, v = np.meshgrid(np.linspace(0, 1, n + 2), np.linspace(0, 1, n + 2))
        keep = (u + v) <= 1
        out.append(t[0] + np.outer(u[keep], t[1] - t[0]) + np.outer(v[keep], t[2] - t[0]))
    return np.concatenate(out)


def seat_plane(samples):
    """(seat footprint centre xy, seat plane z, feet z) of a seated figure's samples."""
    feet = float(samples[:, 2].min())
    height = float(samples[:, 2].max()) - feet
    lowest = {}
    for cell, z in zip(map(tuple, np.floor(samples[:, :2] / 2.0).astype(int)), samples[:, 2]):
        if z < lowest.get(cell, math.inf):
            lowest[cell] = z
    cells = [c for c, z in lowest.items() if feet + 0.2 * height < z < feet + 0.6 * height]
    under = np.array([lowest[c] for c in cells])
    plane = float(np.percentile(under, 20))
    centre = (np.array(cells, float) * 2.0 + 1.0)[np.abs(under - plane) < 3.0].mean(0)
    return centre, plane, feet


def seat_contact(entries, entry, table=None):
    """(need, seat name, seat top, seat plane, feet) of one seated placement among its map's placements: need is the
    z change that puts its seat plane SINK under the seat top, with the binding's current z_offset applied."""
    table = table or bindings()
    plane_xy, plane, feet = seat_plane(placed_samples(entry, table[entry['decoration'].lower()]))
    best = None
    for other in entries:
        binding = table.get(other['decoration'].lower())
        if other is entry or binding is None or other.get('pose'):
            continue
        if abs(other['x'] - entry['x']) > NEIGHBOURS or abs(other['y'] - entry['y']) > NEIGHBOURS:
            continue
        samples = placed_samples(other, binding)
        near = (np.linalg.norm(samples[:, :2] - plane_xy, axis=1) < FOOTPRINT) & (samples[:, 2] < plane + 20.0)
        if near.any() and (best is None or samples[near, 2].max() > best[1]):
            best = (other['source_name'], float(samples[near, 2].max()))
    if best is None:
        if entry.get('floor_z') is None:
            return None
        best = ('floor_z', float(entry['floor_z']))
    return best[1] - plane - SINK, best[0], best[1], plane, feet


def props(project):
    return json.loads((REPO / 'level_generation/projects' / project / 'props.json').read_text())
