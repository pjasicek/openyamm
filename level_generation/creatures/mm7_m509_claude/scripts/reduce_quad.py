"""Triangle budget for a small ambient animal (batch L: keep it low for its size), AFTER the weights (collapse
decimation interpolates vertex groups; humanoid playbook rule), BEFORE the UV unwrap and the retexture. Groups by
piece: the shell (piece 0) to SHELL tris with the head half protected (Decimate vertex group: Head/Neck1 weight > 0.3
at 0.6, so the face keeps more of its triangles), the claws (pieces >= CLAW_MIN) to CLAW_RATIO, the eyes and lids (pieces 1 ..
CLAW_MIN - 1, ~1.2k tris) to EYE_RATIO. Env SHELL_TRIS (3800), CLAW_RATIO (0.25), CLAW_MIN (5), EYE_RATIO (0.35). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
SHELL = int(os.environ.get('SHELL_TRIS', '3800')); CLAW_RATIO = float(os.environ.get('CLAW_RATIO', '0.25'))
CLAW_MIN = int(os.environ.get('CLAW_MIN', '5')); EYE_RATIO = float(os.environ.get('EYE_RATIO', '0.35'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
before = sum(len(p.vertices) - 2 for p in me.polygons)
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
names = [g.name for g in body.vertex_groups]
hk = {i for i, n in enumerate(names) if n in ('Head', 'Neck1')}
prot = body.vertex_groups.new(name='_protect')
for v in me.vertices:
    if pv[v.index] == 0 and sum(e.weight for e in v.groups if e.group in hk) > 0.3:
        prot.add([v.index], 0.6, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
parts = {}
for key, rule in (('shell', lambda a: a == 0), ('claws', lambda a: a >= CLAW_MIN), ('eyes', lambda a: (a > 0) & (a < CLAW_MIN))):
    sel = rule(pv)                                    # on the current mesh (indices change after each split)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in me.vertices:
        v.select = bool(sel[v.index])
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    me = body.data; pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    parts[key] = [o for o in bpy.context.selected_objects if o is not body][-1]
    for o in bpy.data.objects:
        o.select_set(o == body)
rep = {}
for key, o in parts.items():
    tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    ratio = SHELL / tris if key == 'shell' else CLAW_RATIO if key == 'claws' else EYE_RATIO
    m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = min(1.0, ratio)
    if key == 'shell':
        m.vertex_group = '_protect'; m.invert_vertex_group = True
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
    bpy.ops.object.modifier_apply(modifier='dec')
    rep[key] = (tris, sum(len(f.vertices) - 2 for f in o.data.polygons))
for x in bpy.data.objects:
    x.select_set(x is body or x in parts.values())
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.vertex_groups.remove(body.vertex_groups['_protect'])
print('REDUCE', {k: f'{a}->{b}' for k, (a, b) in rep.items()}, 'total', before, '->', sum(len(f.vertices) - 2 for f in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
