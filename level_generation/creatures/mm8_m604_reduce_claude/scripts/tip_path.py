"""Sword-tip (Socket_SwordTip) and right-hand path of a clip, sampled at 60 Hz from a GLB imported as is: position,
speed, and the frames where the speed peaks -> work/tip_<label>.json. Usage: blender -b -P tip_path.py -- <glb> <label> [clip]"""
import json, os, sys, bpy
args = sys.argv[sys.argv.index('--') + 1:]
glb, label = args[:2]; clip = args[2] if len(args) > 2 else 'Attack'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
sc = bpy.context.scene; sc.render.fps = 60
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = next(a for a in bpy.data.actions if a.name.split('|')[-1] == clip or a.name == clip)
rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
fps_import = 24.0  # the glTF importer keys at the scene fps at import time (24)
f0, f1 = act.frame_range
tip = rig.pose.bones.get('Socket_SwordTip'); hand = rig.pose.bones['B_R_Hand']
if tip is None:
    tipobj = bpy.data.objects.get('Socket_SwordTip')
rows = []
n = int(round((f1 - f0) / fps_import * 60))
for k in range(n + 1):
    t = k / 60.0; fr = f0 + t * fps_import
    sc.frame_set(int(fr), subframe=fr - int(fr))
    p = (rig.matrix_world @ tip.head) if tip else tipobj.matrix_world.translation
    h = rig.matrix_world @ hand.head
    rows.append({'t': round(t, 4), 'tip': [round(x, 4) for x in p], 'hand': [round(x, 4) for x in h]})
for i in range(1, len(rows)):
    a, b = rows[i - 1]['tip'], rows[i]['tip']
    rows[i]['speed'] = round(sum((x - y) ** 2 for x, y in zip(a, b)) ** .5 * 60, 3)
rows[0]['speed'] = 0
json.dump({'clip': clip, 'duration': round((f1 - f0) / fps_import, 4), 'rows': rows}, open(os.path.join(HERE, 'work', f'tip_{label}.json'), 'w'))
sp = [r['speed'] for r in rows]
print('TIP', label, clip, 'duration', round((f1 - f0) / fps_import, 4), 'peak', max(sp), 'at', rows[sp.index(max(sp))]['t'])
for r in rows[::6]:
    print(f"  t {r['t']:.3f} speed {r['speed']:6.2f} tip z {r['tip'][2]:.3f}")
