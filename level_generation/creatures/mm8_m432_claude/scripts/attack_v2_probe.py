"""Attack v2 probe: actions, scene keys, Standing grip geometry of the textured master (read only)."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_textured_fit.blend'))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
print('OBJECTS', [(o.name, o.type, o.parent.name if o.parent else None) for o in bpy.data.objects])
print('ACTIONS', [(a.name, tuple(a.frame_range), len(a.layers)) for a in bpy.data.actions])
print('SCENE', sc.render.fps, [k for k in sc.keys()])
print('BONES', [b.name for b in rig.data.bones])
body = bpy.data.objects['Body']
print('ATTR', [a.name for a in body.data.attributes if not a.name.startswith('.')])
grips = {s: json.loads((P / f'work/grip_pose{"" if s == "R" else "_L"}.json').read_text()) for s in 'RL'}
for name in ('Standing', 'Attack', 'Walking'):
    a = bpy.data.actions[name]; rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]
    for f in (a.frame_range[0], (a.frame_range[0] + a.frame_range[1]) / 2):
        sc.frame_set(int(f)); bpy.context.view_layer.update()
        c = {s: armik.W(rig, f'B_{s}_Hand') @ Vector(grips[s]['handle_centre_hand_local']) for s in 'RL'}
        ax = {s: (armik.W(rig, f'B_{s}_Hand').to_3x3().normalized() @ Vector(grips[s]['handle_axis_hand_local'])).normalized() for s in 'RL'}
        sw = armik.W(rig, 'Socket_Sword')
        d = c['L'] - c['R']
        print('GRIP', name, f, 'R', [round(x, 3) for x in c['R']], 'L', [round(x, 3) for x in c['L']], 'L-R along axisR', round(d.dot(ax['R']), 4),
              'perp', round((d - ax['R'] * d.dot(ax['R'])).length, 4), 'axis dot', round(ax['R'].dot(ax['L']), 3),
              'sword y', [round(x, 3) for x in (sw.to_3x3() @ Vector((0, 1, 0)))], 'pelvis', [round(x, 3) for x in armik.W(rig, 'B_Pelvis').translation])
sw = bpy.data.objects['SwordMesh']
ys = [v.co.y for v in sw.data.vertices]
print('SWORD', sw.parent.name if sw.parent else None, sw.parent_type, sw.parent_bone, 'local y range', min(ys), max(ys), 'matrix_world', [list(r) for r in sw.matrix_world])
