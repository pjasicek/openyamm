"""Texture pass step 1: the installed LOD0 as a welded mesh for uv_atlas.py (texpass_uv.py).

Vertices are welded by position separately within the head-set faces (u > 0.5 of the installed 2080x1024 atlas) and
the body faces, so the 2,002 old UV islands no longer constrain the charts, while no chart crosses the head/body
boundary (the head charts get a second, head-only paint). Writes texpass/uv_input.npz.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import BEFORE, TP, head_faces, lod0_arrays, np, read_glb, weld  # noqa: E402

doc, binary = read_glb(BEFORE)
pos, uv, faces = lod0_arrays(doc, binary)
head = head_faces(uv, faces)
verts, welded = weld(pos, faces, head)
head_vertex = np.zeros(len(verts), bool)
head_vertex[welded[head].ravel()] = True
TP.mkdir(exist_ok=True)
np.savez(TP / 'uv_input.npz', positions=verts, faces=welded, head_face=head, head_vertex=head_vertex)
print(f'{len(faces)} triangles, {len(verts)} welded vertices, head faces {head.sum()}')
