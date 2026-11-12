#!/usr/bin/env python3
"""Follow-up 4: a level-zero-only copy of a runtime GLB for tools/build_actor_lods.py (LOD and shadow meshes and the
openyamm_lods extras removed). Usage: lod_source.py <in glb> <out glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glbio import Glb
g = Glb(sys.argv[1]); m0 = g.j['meshes'][0]
keep = [0]; g.j['meshes'] = [m0]; m0.pop('extras', None)
g.compact(); g.save(sys.argv[2]); print('LODSRC', sys.argv[2], len(g.j['meshes']))
