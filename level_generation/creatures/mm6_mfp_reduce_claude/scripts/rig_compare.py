"""Rest-pose and Standing/Attack comparison of the Codex authoring rig (blend) against the installed GLB rig."""
import bpy, sys
glb = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Rig']; W = rig.matrix_world
blend_rest = {b.name: (W @ b.head_local, (W.to_3x3() @ b.matrix_local.to_3x3()).to_quaternion()) for b in rig.data.bones}
blend_acts = {a.name: a for a in bpy.data.actions}
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
g = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE'); GW = g.matrix_world
dp = dq = 0; worst = ''
for b in g.data.bones:
    if b.name not in blend_rest: print('MISSING in blend', b.name); continue
    p, q = blend_rest[b.name]; p2 = GW @ b.head_local
    d = (p - p2).length
    if d > dp: dp, worst = d, b.name
print('REST max head diff mm', round(dp * 1000, 3), worst, 'bones glb', len(g.data.bones), 'blend', len(rig.data.bones))
sc = bpy.context.scene
for name in ('Standing', 'Attack'):
    rig.animation_data.action = blend_acts[name]
    if len(blend_acts[name].slots): rig.animation_data.action_slot = blend_acts[name].slots[0]
    ga = next(a for a in bpy.data.actions if a.name.startswith(name) and a != blend_acts[name] and g.name in a.name or a.name == name + '.001')
    g.animation_data.action = ga
    if len(ga.slots): g.animation_data.action_slot = ga.slots[0]
    worst = 0
    for f in (0, 10, 20):
        sc.frame_set(f)
        for n in ('B_R_Hand', 'Knife', 'B_Head', 'B_L_Foot'):
            worst = max(worst, ((W @ rig.pose.bones[n].head) - (GW @ g.pose.bones[n].head)).length)
    print('POSE', name, ga.name, 'max joint diff mm', round(worst * 1000, 2), 'fps', sc.render.fps)
