"""GLB helpers for the 2026-10-31 texture quality pass (README "Texture quality pass").

The pass edits the installed runtime GLB directly: only UVs (new vertex splits) and images change, so every clip,
skin, LOD geometry, socket and material from the later reduction, Cast v2 and far-LOD repair passes stays as installed.
"""
import sys
import types
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(PROJECT.parent / 'lod_repair_claude' / 'scripts'))
# transfer_textures.py imports build_lods.py, whose MeshLab collapse is not used here.
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
from build_actor_lods import accessor_bytes, append_accessor, read_glb, write_glb  # noqa: E402,F401
from splice_lods import compact, floats  # noqa: E402,F401
from build_lods import rows, source_faces  # noqa: E402,F401

INSTALLED = ROOT / 'assets_source/worlds/mm8/models/mm8_m500.glb'
BEFORE = PROJECT / 'work/before_texpass/mm8_m500.glb'
TP = PROJECT / 'texpass'
# The installed 2080x1024 atlas: body square at u < 1024/2080, head square from 1056/2080.
HEAD_U = 0.5


def mesh_by_name(doc, name):
    return next(i for i, m in enumerate(doc['meshes']) if m['name'] == name)


def lod0_arrays(doc, binary):
    p = doc['meshes'][mesh_by_name(doc, 'Body')]['primitives'][0]
    pos = floats(doc, binary, p['attributes']['POSITION'])
    uv = floats(doc, binary, p['attributes']['TEXCOORD_0'])
    faces = source_faces(doc, binary, p)
    return pos, uv, faces


def head_faces(uv, faces):
    return uv[faces].mean(1)[:, 0] > HEAD_U


def weld(pos, faces, groups):
    """Weld vertices by position within each face group (groups never share a vertex, so no chart crosses them)."""
    keys = {}
    out = np.zeros_like(faces)
    verts = []
    for f, tri in enumerate(faces):
        for k, v in enumerate(tri):
            key = (int(groups[f]),) + tuple(np.round(pos[v], 6))
            if key not in keys:
                keys[key] = len(verts)
                verts.append(pos[v])
            out[f, k] = keys[key]
    return np.array(verts), out
