"""Per clip: the jaw's opening angle relative to the head, measured against the REST pose (signed: + = mouth opens
down), from the MM9 jaw-weighted vertices' centroid direction about the jaw pivot. Args: <rig blend> <head> <jawpivot bone> <jaw bones>"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
HEAD, PIV, JAW = argv[1], argv[2], argv[3].split(',')
arm = bpy.data.objects['MM9_Rig']
sc = bpy.context.scene
def frame_vals():
    hm = arm.matrix_world @ arm.pose.bones[HEAD].matrix
    inv = hm.inverted()
    piv = inv @ (arm.matrix_world @ arm.pose.bones[PIV].head)
    out = []
    for j in JAW:
        jm = arm.matrix_world @ arm.pose.bones[j].matrix
        out.append(inv @ jm)
    return piv, out
# reference = rest
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
piv0, J0 = frame_vals()
# jaw tip = farthest jaw-weighted vertex from the pivot, in rest
tips = []
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        if o.vertex_groups[g.group].name in JAW:
            tips.append((o.matrix_world @ v.co, o.vertex_groups[g.group].name))
hm0 = (arm.matrix_world @ arm.pose.bones[HEAD].matrix).inverted()
tipw, tipb = max(tips, key=lambda t: (t[0] - arm.matrix_world @ arm.pose.bones[PIV].head).length)
k = JAW.index(tipb)
tip_local_j = (arm.matrix_world @ arm.pose.bones[tipb].matrix).inverted() @ tipw
tip0 = hm0 @ tipw
lat = (hm0.to_3x3() @ Vector((1, 0, 0))).normalized()   # world +X in head space: + = opens
arm.animation_data_create()
for act in bpy.data.actions:
    arm.animation_data.action = act
    f0, f1 = act.frame_range
    angs = []
    for f in np.linspace(f0, f1, 40):
        sc.frame_set(int(f), subframe=f - int(f))
        hm = arm.matrix_world @ arm.pose.bones[HEAD].matrix
        tw = (arm.matrix_world @ arm.pose.bones[tipb].matrix) @ tip_local_j
        t = hm.inverted() @ tw
        a = (tip0 - piv0); b = (t - piv0)
        # signed angle in the head's sagittal plane: use world-ish: compare head-local components
        ang = math.degrees(a.angle(b))
        sgn = 1 if a.cross(b).dot(lat) >= 0 else -1
        angs.append(sgn * ang)
    print('JAWANG %-10s min %5.1f max %5.1f mean %5.1f' % (act.name, min(angs), max(angs), sum(angs) / len(angs)))
