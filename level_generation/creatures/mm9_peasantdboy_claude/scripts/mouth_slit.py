"""The mouth slit's rim (the 18-edge head boundary loop nearest the mouth, as build_export_v2.py's mouth_cap finds it)
in glTF rest coordinates of the export (x, y = z + LIFT, z = -y), for face_paint_fix.py's closed-mouth repaint.
Writes work/mouth_slit.json. Args (Blender): <blend> [lift 0.4825]"""
import bpy, bmesh, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
LIFT = float(a[1]) if len(a) > 1 else 0.4825
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
hl = bm.faces.layers.int['head']
bnd = {e for e in bm.edges if e.is_boundary and e.link_faces[0][hl]}
loops = []
while bnd:
    e = bnd.pop(); lp = [e]; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for f in v.link_edges:
                if f in bnd:
                    bnd.discard(f); lp.append(f); st.append(f)
    loops.append(lp)
M = Vector((0, -0.061, 0.69))
best = min(loops, key=lambda lp: min((v.co - M).length for e in lp for v in e.verts))
pts = sorted({(round(v.co.x, 5), round(v.co.z + LIFT, 5), round(-v.co.y, 5)) for e in best for v in e.verts})
json.dump(pts, open(a[0].rsplit('/work/', 1)[0] + '/work/mouth_slit.json', 'w'))
print('MOUTHSLIT', len(best), 'x', min(p[0] for p in pts), max(p[0] for p in pts), 'y', min(p[1] for p in pts), max(p[1] for p in pts))
