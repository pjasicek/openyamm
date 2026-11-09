"""Re-measure soles on the baked clips (tilt, roll, pitch, lowest point) and render clip frames: full body front/side
plus hand and foot close-ups. Args: blend tag."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
arm = bpy.data.objects['Mage_Rig']; mesh = bpy.data.objects['Mage']; me = mesh.data; scene = bpy.context.scene
co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
sole = {s: np.where((co[:, 2] < 0.04) & (co[:, 0] * k > 0.05))[0] for s, k in (('L', 1), ('R', -1))}
def state():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return P
def set_action(act):
    arm.animation_data.action = act
    if getattr(act, 'slots', None): arm.animation_data.action_slot = act.slots[0]
for name in ('Idle_9', 'Walking', 'Running', 'Idle_9_src', 'Walking_src', 'Running_src'):
    act = bpy.data.actions[name]; set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range); grounded = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f); P = state()
        for s in ('L', 'R'):
            sp = P[sole[s]]; c = sp.mean(0); n = np.linalg.svd(sp - c)[2][2]; n = n * np.sign(n[2])
            h = sp[:, 2].min()
            if h < 0.03:
                grounded.append((s, round(math.degrees(math.acos(min(1, n[2]))), 1), round(float(h), 3)))
    tilts = [g[1] for g in grounded]; lows = [g[2] for g in grounded]
    print('SOLE', name, 'grounded samples', len(grounded), 'tilt mean/max', round(float(np.mean(tilts)), 1) if tilts else None,
          max(tilts) if tilts else None, 'lowest z', min(lows) if lows else None)
common.workbench_clay(scene); scene.display.shading.color_type = 'SINGLE'; scene.display.shading.single_color = (0.72, 0.72, 0.7)
out = os.path.join(common.REVIEW, tag); os.makedirs(out, exist_ok=True)
SHOTS = {'Running': (0, 4, 8, 12), 'Walking': (0, 6, 12, 18), 'Idle_9': (0, 24)}
for name, frames in SHOTS.items():
    set_action(bpy.data.actions[name])
    for f in frames:
        scene.frame_set(f)
        P = state(); hips = arm.matrix_world @ arm.pose.bones['mixamorig:Hips'].head
        tx, ty = float(hips.x), float(hips.y)
        common.render_views(os.path.join(out, f'{name}_{f:02d}'), 0.9, 1.9, views=('front', 'left'), resolution=(360, 520), target=(tx, ty))
        for side in ('Left', 'Right'):
            h = arm.matrix_world @ arm.pose.bones[f'mixamorig:{side}Hand'].tail
            common.render_views(os.path.join(out, f'{name}_{f:02d}_hand{side[0]}'), float(h.z), 0.2, views=('three_quarter',), resolution=(260, 260), target=(float(h.x), float(h.y)))
        common.render_views(os.path.join(out, f'{name}_{f:02d}_feet'), 0.12, 0.5, views=('front', 'left'), resolution=(360, 360), target=(tx, ty))
