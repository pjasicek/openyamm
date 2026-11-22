#!/usr/bin/env python3
"""Reduce the mirrored voxel body (work/voxel_body.npz) to BODY_TRIS triangles with MeshLab's quadric edge collapse
(quality threshold 0.5, planar quadrics, normals preserved) -> work/voxel_body_reduced.npz (vertices, triangles).
Run with claude_shared/meshlab_venv/bin/python. Usage: reduce_voxel.py [tris]"""
import sys, pymeshlab
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
n = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
import numpy as np
D = np.load(ROOT / 'work/voxel_body.npz')
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=D['co'].astype(np.float64), face_matrix=D['tris'].astype(np.int32)))
print('TOPO', ms.get_topological_measures())
print('IN', ms.current_mesh().face_number())
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=n, qualitythr=0.5, preservenormal=True,
                                            planarquadric=True, optimalplacement=True, autoclean=True)
import numpy as np
m = ms.current_mesh()
np.savez(ROOT / 'work/voxel_body_reduced.npz', co=m.vertex_matrix(), tris=m.face_matrix())
print('OUT', ms.current_mesh().face_number())
