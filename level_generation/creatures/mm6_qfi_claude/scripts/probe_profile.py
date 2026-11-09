"""Diagnostic: per 2 cm of height, the central torso ring's half-width, depth and perimeter and how many loops the
horizontal slice has (arms separate below the armpits). Prints PROFILE lines."""
import bpy, bmesh
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step1.blend'))
ob = bpy.data.objects['Queen']
BASE = bmesh.new(); BASE.from_mesh(ob.data)
for z in np.arange(1.1, 2.3, 0.02):
    bm = BASE.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, 0, z)),
                                 plane_no=Vector((0, 0, 1)))
    pts = np.array([tuple(v.co) for v in res['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
    bm.free()
    if len(pts) == 0:
        continue
    central = pts[np.abs(pts[:, 0]) < 0.3]
    print(f'PROFILE z={z:.2f} n={len(pts)} xmin={pts[:,0].min():.3f} xmax={pts[:,0].max():.3f} '
          f'central_half={np.abs(central[:,0]).max() if len(central) else 0:.3f} '
          f'ymin={central[:,1].min() if len(central) else 0:.3f} ymax={central[:,1].max() if len(central) else 0:.3f}')
