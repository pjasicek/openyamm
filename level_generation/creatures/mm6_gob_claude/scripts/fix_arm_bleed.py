"""Remove upper-arm weight that bled onto the torso (chest, back, lats, neck) in the proxy weight transfer.

Torso-side skin within the upper-arm cylinder's inner side follows the arm whenever it swings, dragging lats into
the chest and wringing the armpit. For every non-sword vertex, the distance inside the arm cylinder's inner edge
(rest A-pose, measured in x at the vertex height) fades the <Side>Arm weight out over 6 cm; the removed weight goes
to the clavicle above the shoulder joint and to Spine2 below it.
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector

rig = bpy.data.objects['Peasant_Rig']; mesh = bpy.data.objects['Peasant']; me = mesh.data
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
sword = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if part[p.index] == PARTS.index('Sword'):
        sword[list(p.vertices)] = True
RADIUS = 0.05
moved_total = {}
for side in ('Left', 'Right'):
    arm = rig.data.bones[f'mixamorig:{side}Arm']
    head = rig.matrix_world @ arm.head_local; tail = rig.matrix_world @ arm.tail_local
    g_arm = mesh.vertex_groups[f'mixamorig:{side}Arm']
    g_sh = mesh.vertex_groups[f'mixamorig:{side}Shoulder']
    g_sp = mesh.vertex_groups['mixamorig:Spine2']
    moved = 0
    for v in me.vertices:
        if sword[v.index]:
            continue
        w = next((g.weight for g in v.groups if g.group == g_arm.index), 0.0)
        if w <= 0.0:
            continue
        co = mesh.matrix_world @ v.co
        # x of the arm axis at this height (clamped to the bone), inner edge of the arm cylinder
        t = min(1.0, max(0.0, (head.z - co.z) / max(head.z - tail.z, 1e-6)))
        axis_x = abs(head.x + (tail.x - head.x) * t)
        d = abs(co.x) - (axis_x - RADIUS)
        keep = min(1.0, max(0.0, 0.5 + d / 0.06))
        if keep >= 1.0:
            continue
        removed = w * (1.0 - keep)
        g_arm.add([v.index], w * keep, 'REPLACE')
        target = g_sh if co.z > head.z - 0.02 else g_sp
        cur = next((g.weight for g in v.groups if g.group == target.index), 0.0)
        target.add([v.index], cur + removed, 'REPLACE')
        moved += 1
    moved_total[side] = moved
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
# smooth the new arm/torso boundary around each armpit so no skin fin is left between the two influences
body = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if part[p.index] == PARTS.index('Body'):
        body[list(p.vertices)] = True
for v in me.vertices:
    v.select = False
for side in ('Left', 'Right'):
    head = rig.matrix_world @ rig.data.bones[f'mixamorig:{side}Arm'].head_local
    for v in me.vertices:
        if body[v.index] and ((mesh.matrix_world @ v.co) - head).length < 0.13:
            v.select = True
bpy.ops.object.mode_set(mode='EDIT')
for name in ('mixamorig:LeftArm', 'mixamorig:RightArm', 'mixamorig:LeftShoulder', 'mixamorig:RightShoulder',
             'mixamorig:Spine2'):
    mesh.vertex_groups.active_index = mesh.vertex_groups[name].index
    bpy.ops.object.vertex_group_smooth(group_select_mode='ACTIVE', factor=0.5, repeat=4)
bpy.ops.object.mode_set(mode='OBJECT')
# shoulder armour (pauldrons, their spikes, strap ends) follows the skin underneath it: average the weights of the
# three nearest skin vertices, so the plates cannot separate from or be pierced by the shoulder skin
from mathutils.kdtree import KDTree
heads = [rig.matrix_world @ rig.data.bones[f'mixamorig:{side}Arm'].head_local for side in ('Left', 'Right')]
skin_idx = [v.index for v in me.vertices if body[v.index] and min(((mesh.matrix_world @ v.co) - h).length
                                                                       for h in heads) < 0.24]
kd = KDTree(len(skin_idx))
for k, i in enumerate(skin_idx):
    kd.insert(mesh.matrix_world @ me.vertices[i].co, k)
kd.balance()
shell = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if PARTS[part[p.index]] in ('Armor', 'Spikes', 'Leather'):
        shell[list(p.vertices)] = True
copied = 0
for v in me.vertices:
    if not shell[v.index]:
        continue
    co = mesh.matrix_world @ v.co
    if min((co - h).length for h in heads) > 0.20:
        continue
    near = kd.find_n(co, 3)
    acc = {}
    total = 0.0
    for _, k, d in near:
        wt = 1.0 / max(d, 1e-4); total += wt
        for g in me.vertices[skin_idx[k]].groups:
            acc[g.group] = acc.get(g.group, 0.0) + g.weight * wt
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([v.index])
    for gi, w in acc.items():
        mesh.vertex_groups[gi].add([v.index], w / total, 'REPLACE')
    copied += 1
print('SHELL weights copied', copied)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.wm.save_mainfile()
print('ARM BLEED fixed', moved_total)
