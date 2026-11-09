"""Mirror the reduced, weighted 'Body' from its right half (-X) so it is exactly symmetric again (voxel passes and
decimation are not). bmesh.ops.symmetrize copies the deform weights to the mirrored half; there the left/right bones are
swapped. Args: <in blend> <out blend> <report json> <L=R pairs comma, e.g. Xearbase=Xearbase1> (other X.. bones: X <-> X01)
"""
import bpy, bmesh, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
extra = dict(p.split('=') for p in argv[3].split(',')) if len(argv) > 3 and argv[3] else {}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
arm = bpy.data.objects['MM9_Rig']
me = body.data
names = [b.name for b in arm.data.bones]
swap = {}
for n in names:
    if n + '01' in names:
        swap[n] = n + '01'; swap[n + '01'] = n
for a, b in extra.items():
    swap[a] = b; swap[b] = a
for n in names:
    if n not in body.vertex_groups:
        body.vertex_groups.new(name=n)
before = len(me.polygons)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='-X', dist=1e-5)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
dl = bm.verts.layers.deform.active
gn = {g.index: g.name for g in body.vertex_groups}
gi = {g.name: g.index for g in body.vertex_groups}
swapped = 0
for v in bm.verts:
    if v.co.x > 1e-6:
        d = v[dl]
        items = list(d.items())
        d.clear()
        for k, w in items:
            d[gi[swap.get(gn[k], gn[k])]] = w
        swapped += 1
    elif abs(v.co.x) <= 1e-6:
        # midline vertices: left and right share the weight evenly
        d = v[dl]
        items = list(d.items())
        acc = {}
        for k, w in items:
            n = gn[k]
            if n in swap:
                acc[n] = acc.get(n, 0) + w / 2
                acc[swap[n]] = acc.get(swap[n], 0) + w / 2
            else:
                acc[n] = acc.get(n, 0) + w
        d.clear()
        for n, w in acc.items():
            d[gi[n]] = w
cl = bm.verts.layers.int['chain']
for v in bm.verts:
    if v.co.x > 1e-6 and v[cl] in (1, 3):
        v[cl] = v[cl] - 1      # fit_quad.py order: 0 fl, 1 fr, 2 hl, 3 hr
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
co = np.array([tuple(v.co) for v in me.vertices])
key = {tuple(np.round(p, 5)): i for i, p in enumerate(co)}
miss = sum(1 for p in co if (round(-p[0], 5) + 0.0, round(p[1], 5), round(p[2], 5)) not in key)
rep = {'faces_before': before, 'faces_after': len(me.polygons), 'verts': len(co), 'swapped': swapped, 'mirror_missing': miss}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'))
print('SYMRIG ' + json.dumps(rep))
