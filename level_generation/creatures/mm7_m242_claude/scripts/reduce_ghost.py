"""Triangle budget AFTER the weights (playbook: collapse decimation interpolates the vertex groups, and the bone pieces
are rigid, so their weights survive exactly). Per class, separated, decimated and joined back:
skull (piece 0) SKULL, cape/hood shell (piece 1) CAPE, robe shreds (other cloth) SHREDS, claws (bone pieces beyond
|x| 0.52) CLAWS, other bones (spine, ribs, arm bones) BONES. Reports pieces that fell under 4 triangles.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: int(os.environ.get(k, d))
TGT = {'skull': E('SKULL', 1100), 'cape': E('CAPE', 900), 'shreds': E('SHREDS', 2600), 'claws': E('CLAWS', 1100),
       'bones': E('BONES', 2500)}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
cl = np.zeros(len(me.vertices), np.int32); me.attributes['cloth'].data.foreach_get('value', cl)
co = np.array([tuple(v.co) for v in me.vertices])
cx = {p: abs(co[pv == p][:, 0].mean()) for p in set(pv.tolist())}
cls = np.array(['skull' if p == 0 else 'cape' if p == 1 else 'shreds' if c else ('claws' if cx[p] > 0.52 else 'bones')
                for p, c in zip(pv, cl)])
before = sum(len(p.vertices) - 2 for p in me.polygons)
parts = {}
for k in TGT:
    for o in bpy.data.objects:
        o.select_set(o == body)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    me = body.data
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    cl = np.zeros(len(me.vertices), np.int32); me.attributes['cloth'].data.foreach_get('value', cl)
    sel = np.array(['skull' if p == 0 else 'cape' if p == 1 else 'shreds' if c else ('claws' if cx[p] > 0.52 else 'bones')
                    for p, c in zip(pv, cl)]) == k
    for v in me.vertices:
        v.select = bool(sel[v.index])
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    parts[k] = [o for o in bpy.context.selected_objects if o is not body][-1]
rep = {}
for k, o in parts.items():
    t = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if t > TGT[k]:
        # pieces of <= KEEP_TRIS triangles keep their shape (tiny vertebrae and phalanx tips collapsed to slivers)
        pp = np.zeros(len(o.data.vertices), np.int32); o.data.attributes['piece'].data.foreach_get('value', pp)
        pt = {}
        for f in o.data.polygons:
            pt[int(pp[f.vertices[0]])] = pt.get(int(pp[f.vertices[0]]), 0) + len(f.vertices) - 2
        small = [v.index for v in o.data.vertices if pt.get(int(pp[v.index]), 0) <= E('KEEP_TRIS', 24)]
        kg = o.vertex_groups.new(name='_keep'); kg.add(small, 1.0, 'REPLACE')
        m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TGT[k] / t
        m.vertex_group = '_keep'; m.invert_vertex_group = True
        for x in bpy.data.objects:
            x.select_set(x == o)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
        bpy.ops.object.modifier_apply(modifier='dec')
        o.vertex_groups.remove(o.vertex_groups['_keep'])
    rep[k] = f"{t}->{sum(len(f.vertices) - 2 for f in o.data.polygons)}"
for x in bpy.data.objects:
    x.select_set(x is body or x in parts.values())
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
per = {}
for f in me.polygons:
    k = int(pc[f.vertices[0]]); per[k] = per.get(k, 0) + len(f.vertices) - 2
thin = sorted(k for k, n in per.items() if n < 4)
print('REDUCE', rep, 'total', before, '->', sum(len(f.vertices) - 2 for f in me.polygons), '| pieces under 4 tris:', thin)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
