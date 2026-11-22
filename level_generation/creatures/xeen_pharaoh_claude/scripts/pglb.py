"""Shared helpers for the pharaoh scripts: load a GLB with claude_shared/floor/glb_pose, named nodes, LOD0 data."""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
import glb_pose  # noqa: E402,F401
from glb_pose import Glb, Model, trs_matrix, matrix_quaternion, quaternion_matrix, slerp  # noqa: E402,F401


def load(path):
    g = Glb(path)
    m = Model(g)
    names = {n.get('name'): i for i, n in enumerate(g.json['nodes'])}
    return g, m, names


def rest_world(m):
    return m.world({})


def lod0_body(m):
    """LOD0 skinned primitive (largest): positions, triangles, joints, weights; dominant joint node per vertex."""
    prim = max((p for p in m.primitives if p['skinned']), key=lambda p: len(p['triangles']))
    dom = np.array(m.joints)[prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(1)]]
    return prim, dom
