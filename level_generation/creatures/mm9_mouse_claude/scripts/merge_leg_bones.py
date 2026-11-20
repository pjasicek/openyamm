"""One bone per paw on the UV'd mesh (uv_v1 was laid and sent to Meshy with the first three-bone legs; rig_mouse.py
now makes the single paw bone directly). Leg<X>_up/_low are dropped, Leg<X>_paw becomes Leg<X> under Bone05 (not
connected), and its weight becomes paw + low + up: exactly rig_mouse.py's current leg weight. Topology and UVs are
unchanged. Args: <in blend> <out blend>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
legs = ('FL', 'FR', 'HL', 'HR')
me = body.data
for leg in legs:
    gs = [body.vertex_groups.get(f'Leg{leg}_{p}') for p in ('paw', 'low', 'up')]
    gi = {g.index: g for g in gs if g}
    acc = {}
    for v in me.vertices:
        w = sum(g.weight for g in v.groups if g.group in gi)
        if w > 0:
            acc[v.index] = w
    for g in gs:
        if g:
            body.vertex_groups.remove(g)
    ng = body.vertex_groups.new(name=f'Leg{leg}')
    for i, w in acc.items():
        ng.add([i], min(w, 1.0), 'REPLACE')
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
for leg in legs:
    paw = eb[f'Leg{leg}_paw']
    paw.use_connect = False
    paw.parent = eb['Bone05']
    paw.name = f'Leg{leg}'
    for p in ('low', 'up'):
        eb.remove(eb[f'Leg{leg}_{p}'])
bpy.ops.object.mode_set(mode='OBJECT')
print('MERGED', [b.name for b in arm.data.bones])
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
