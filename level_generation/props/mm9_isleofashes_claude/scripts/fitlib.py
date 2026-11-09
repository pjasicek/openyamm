"""Placement fit: a source model's raw LOD0 vertices (glTF = LithTech local axes x 2.56) against the baked BModel
of each placement in the old isle ODM. Mapping to OpenYAMM local: (x, y, z)_LT -> (m * x, z, y), rotated about z by
the yaw, scaled, translated so the bounding-box centres coincide; the fit reports the median vertex distance."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE / 'scripts'))
from glbio import positions  # noqa: E402

_odm = None


def bmodels():
    global _odm
    if _odm is None:
        from util.map_export import parse_odm_file
        payload = parse_odm_file(REPO / 'assets_editor_dev/worlds/mm9/maps/isleofashes.odm')['payload']
        _odm = {b['name']: b for b in payload['bmodels']}
    return _odm


def bmodel_vertices(name):
    return np.array([[a['x'], a['y'], a['z']] for a in bmodels()[name]['vertices']], float)


def rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def lt_local_to_oy(g, mirror=1.0):
    return np.stack([mirror * g[:, 0], g[:, 2], g[:, 1]], 1)


def fit(local_oy, bverts, yaw, scale):
    inst = (local_oy * scale) @ rot(yaw).T
    centre_b = (bverts.min(0) + bverts.max(0)) / 2
    centre_i = (inst.min(0) + inst.max(0)) / 2
    t = centre_b - centre_i
    d, _ = cKDTree(bverts).query(inst + t)
    return float(np.median(d)), float(np.max(d)), t
