"""Dihedral angles between neighbouring faces (degrees): the body at the chest and shoulders (part 0, centroid
z 1.2-1.5, |x| < 0.3) against the authored head (part 3: skull/muzzle hull; crown shards reported apart by
centroid above the brow and behind the head joint). Usage: blender -b -P dihedral.py -- <blend>"""
import math, os, sys, bpy, bmesh
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
me = bpy.data.objects['CrystalWalker'].data
bm = bmesh.new(); bm.from_mesh(me); lay = bm.faces.layers.int.get('part')
def cls(f):
    p = f[lay] if lay is not None else 0; c = f.calc_center_median()
    if p == 0 and 1.2 < c.z < 1.5 and abs(c.x) < .3:
        return 'body'
    if p == 3:
        return 'head'
    return None
groups = {'body': [], 'head': []}
for e in bm.edges:
    if len(e.link_faces) != 2:
        continue
    f1, f2 = e.link_faces; c1, c2 = cls(f1), cls(f2)
    if c1 and c1 == c2:
        groups[c1].append(math.degrees(e.calc_face_angle(0)))
for k, v in groups.items():
    v = np.array(v)
    print(f'DIHEDRAL {k}: edges {len(v)} median {np.median(v):.1f} p75 {np.percentile(v,75):.1f} p90 {np.percentile(v,90):.1f} '
          f'share under 2 deg {np.mean(v < 2):.2f} under 5 deg {np.mean(v < 5):.2f}')
