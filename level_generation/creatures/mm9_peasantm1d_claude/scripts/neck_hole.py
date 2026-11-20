"""Fill the see-through hole under the right jaw (ear sweep 2026-11-02, `claude_shared/mm9_overview/ear_sweep_20261102.png`
rows 1-2: "a small pale grey triangle under the jaw" on both tiers = the render background seen through a 5-edge boundary loop
(two missing triangles meeting at a point, a bow-tie), at the side of the neck under the right jaw; in the export GLB its
centre is (-0.038, 1.578, 0.054), 1.2 cm across. Not paint and not a shirt lace: the head set's neck skin around it is
continuous. Present since geo_fix.py deleted the two 34 cm slivers from the jaw to the right collar (their root faces).
Boundary loops of at most MAXE edges whose centre lies in the neck box (|x| < NECK_X, NECK_Z, front half; Blender rest
coordinates of this blend) are filled and triangulated; every new face takes the UVs (UVMap and HeadUV) its corners have in a
rim face when they lie in one UV island (the patch continues the neck skin's paint), else the nearest rim face's mean texel; and the face attributes (head, hand) of the largest rim face.
Positions and faces only, no vertex moves. Args (Blender): <in blend> <out blend> [list]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
MAXE = 8
LIST = len(a) > 2 and a[2] == 'list'
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world
bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
uvs = [bm.loops.layers.uv[n] for n in ('UVMap', 'HeadUV') if n in bm.loops.layers.uv]
ilayers = [bm.faces.layers.int[n] for n in ('head', 'hand') if n in bm.faces.layers.int]
zs = [(mw @ v.co).z for v in bm.verts]
top = max(zs)
seen = set(); loops = []
for e in bm.edges:
    if not e.is_boundary or e.index in seen:
        continue
    lp = [e]; seen.add(e.index); st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y.index not in seen:
                    seen.add(y.index); lp.append(y); st.append(y)
    loops.append(lp)
rep = []
NECK = json.loads(a[3]) if len(a) > 3 else None     # {"x": [x0, x1], "y": [y0, y1], "z": [z0, z1]} Blender coordinates
for lp in loops:
    c = np.mean([tuple(mw @ v.co) for x in lp for v in x.verts], 0)
    rim = {x.link_faces[0] for x in lp}
    info = {'edges': len(lp), 'centre': c.round(4).tolist(), 'head': [int(f[ilayers[0]]) for f in rim][:3] if ilayers else []}
    if LIST:
        if len(lp) <= MAXE:
            print('LOOP', json.dumps(info))
        continue
    if len(lp) > MAXE or NECK is None or not all(NECK[k][0] < c[i] < NECK[k][1] for i, k in enumerate('xyz')):
        continue
    vuv = {}
    for f in rim:
        for l in f.loops:
            vuv.setdefault(l.vert, [tuple(l[u].uv) for u in uvs])
    ref = max(rim, key=lambda f: f.calc_area())
    new = bmesh.ops.holes_fill(bm, edges=lp, sides=0)['faces']
    if not new:
        new = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=lp)['geom']
        new = [g for g in new if isinstance(g, bmesh.types.BMFace)]
    new = bmesh.ops.triangulate(bm, faces=new, quad_method='BEAUTY', ngon_method='BEAUTY')['faces']
    for f in new:
        for il in ilayers:
            f[il] = ref[il]
        f.material_index = ref.material_index
        f.smooth = ref.smooth
        for k, u in enumerate(uvs):
            cu = np.array([vuv[l.vert][k] for l in f.loops])
            if np.ptp(cu, 0).max() <= 0.05:               # corners in one UV island: continue the paint
                for l, uv in zip(f.loops, cu):
                    l[u].uv = tuple(uv)
            else:                                         # across a seam: the nearest rim face's mean texel (flat patch)
                c0 = np.array(tuple(f.calc_center_median()))
                near = min(rim, key=lambda g: np.linalg.norm(np.array(tuple(g.calc_center_median())) - c0))
                m = tuple(np.mean([tuple(l[u].uv) for l in near.loops], 0))
                for l in f.loops:
                    l[u].uv = m
                info.setdefault('flat', []).append(k)
    info['faces'] = len(new)
    info['uv_spread'] = [round(float(np.ptp(np.array([vuv[v][k] for x in lp for v in x.verts]), 0).max()), 4) for k in range(len(uvs))]
    rep.append(info)
if not LIST:
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    bpy.ops.wm.save_as_mainfile(filepath=a[1])
    print('NECK_HOLE', json.dumps(rep))
