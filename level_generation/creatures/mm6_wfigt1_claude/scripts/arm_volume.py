"""Upper-arm thickness audit: for bands along the left upper arm (t = 0.2..0.9 of shoulder->elbow), the mean distance
of the arm skin to the bone axis, split into the four quadrants of the bone's rest frame (front/back/top/bottom), at
rest and per frame of a clip. Arm skin = vertices within 0.16 m of the segment at rest with t in band. Args: blend clip"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, clip = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, blend))
arm = bpy.data.objects['Werewolf_Rig']; mesh = bpy.data.objects['Werewolf']; W = arm.matrix_world


def verts():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return P


def frame_of(side):
    pb = arm.pose.bones[side + 'Arm']
    A = np.array(W @ pb.head); B = np.array(W @ arm.pose.bones[side + 'ForeArm'].head)
    M = (W @ pb.matrix).to_3x3().normalized()
    return A, B, np.array(M @ Vector((1, 0, 0))), np.array(M @ Vector((0, 0, 1)))


def measure(P, side, sel=None):
    A, B, X, Z = frame_of(side)
    d = B - A; L = np.linalg.norm(d); u = d / L
    t = (P - A) @ u / L
    r = P - A - np.outer(t * L, u)
    dist = np.linalg.norm(r, axis=1)
    if sel is None:
        sel = (t > 0.2) & (t < 0.9) & (dist < 0.16)
    ang = np.degrees(np.arctan2(r @ Z, r @ X))
    out = []
    for lo, hi in ((-45, 45), (45, 135), (135, 225), (-135, -45)):
        a = ((ang - lo) % 360) < (hi - lo)
        out.append(float(dist[sel & a].mean()) if (sel & a).any() else 0)
    return sel, np.round(np.array(out) * 100, 1)


arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
P0 = verts()
sels = {}
for side in ('Left',):
    sels[side], r0 = measure(P0, side)
    print('VOL rest', side, 'radius cm per quadrant (+X, +Z, -X, -Z)', r0, 'verts', int(sels[side].sum()))
a = bpy.data.actions[clip]; arm.animation_data.action = a
if a.slots: arm.animation_data.action_slot = a.slots[0]
for f in range(int(a.frame_range[1]) + 1):
    bpy.context.scene.frame_set(f)
    _s, r = measure(verts(), 'Left', sels['Left'])
    print('VOL', clip, f, r, 'min ratio', round(float((r / np.maximum(r0, 1e-3)).min()), 2))
