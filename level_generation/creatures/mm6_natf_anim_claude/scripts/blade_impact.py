"""Blade tip track over a clip in the master (60 Hz): tip = the ForearmBlade mesh vertex farthest from the forearm
bone along the blade; prints per-frame tip position, speed and forward (-Y, toward the target) speed, and the impact
estimate = the frame of peak tip speed while the tip is in front of the chest and moving forward.
Usage: blender -b -P blade_impact.py -- <blend> <action>"""
import os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); sc = bpy.context.scene; sc.render.fps = 60
rig = bpy.data.objects['Rig']; blade = bpy.data.objects['ForearmBlade']
act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
dg = bpy.context.evaluated_depsgraph_get()
def tip():
    ev = blade.evaluated_get(dg); m = ev.to_mesh(); fb = rig.matrix_world @ rig.pose.bones['B_R_Forearm'].head
    pts = [ev.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
    return max(pts, key=lambda p: (p - fb).length)
f0, f1 = (int(x) for x in act.frame_range); prev = None; best = (0, None)
for f in range(f0, f1 + 1):
    sc.frame_set(f); p = tip(); chest = rig.matrix_world @ rig.pose.bones['B_Spine2'].head
    if prev is not None:
        v = (p - prev) * 60; fwd = -v.y; sp = v.length
        front = p.y < chest.y - 0.15
        if front and fwd > 0 and sp > best[0]: best = (sp, f)
        if f % 4 == 0: print(f'  f{f:3d} t {f / 60:.3f} tip ({p.x:.2f},{p.y:.2f},{p.z:.2f}) speed {sp:5.2f} fwd {fwd:5.2f}')
    prev = p
print('IMPACT', a[1], 'frame', best[1], 'time', None if best[1] is None else round(best[1] / 60, 4), 's, tip speed', round(best[0], 2), 'm/s')
