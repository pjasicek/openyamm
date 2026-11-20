"""Separate limb skin from torso skin using Meshy's auto-rig weights as a region mask (same mesh, rig_v1 job).

The proxy weight transfer (and fix_arm_bleed's cylinder test) left inner-elbow/forearm skin with 30-60 % Spine2
weight: when the arm lifted, that skin stayed with the chest and stretched 6-9x. Meshy's weights segment the
surface correctly (arm skin is on arm bones, torso skin is not), but its joints sit elsewhere, so only its
region membership is used:
  - Body vertex that Meshy puts >= 0.7 on one limb chain: our weights outside that limb (+ its clavicle/hip) go,
  - Body vertex with <= 0.05 on a limb chain: our weights on that limb's bones go,
  - skirt strips (Leather between the legs) follow the pelvis: Hips 0.75 + nearer thigh 0.25, centre strips Hips 1.
Then renormalisation (no smoothing: it would bleed torso weight back onto arm skin).
Run after refit_hands / fix_arm_bleed (works on any blend with the final mesh).
"""
import bpy, os, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mesh = bpy.data.objects['Peasant']; me = mesh.data; rig = bpy.data.objects['Peasant_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
vpart = np.full(len(me.vertices), -1)
for p in me.polygons:
    vpart[list(p.vertices)] = part[p.index]

# Meshy rigged mesh (temporary import)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/rig_v1/result_rigged_character_glb_url.glb'))
new = [o for o in bpy.data.objects if o not in before]
mm = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
mnames = [g.name for g in mm.vertex_groups]
mco = [mm.matrix_world @ v.co for v in mm.data.vertices]
kd = KDTree(len(mco))
for i, c in enumerate(mco):
    kd.insert(c, i)
kd.balance()
CHAINS = {
    'armR': ('RightArm', 'RightForeArm', 'RightHand'), 'armL': ('LeftArm', 'LeftForeArm', 'LeftHand'),
    'legR': ('RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase'), 'legL': ('LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase'),
}
OURS = {
    'armR': lambda n: n.startswith(('mixamorig:RightArm', 'mixamorig:RightForeArm', 'mixamorig:RightHand', 'RightForeArmTwist')),
    'armL': lambda n: n.startswith(('mixamorig:LeftArm', 'mixamorig:LeftForeArm', 'mixamorig:LeftHand', 'LeftForeArmTwist')),
    'legR': lambda n: n.startswith(('mixamorig:RightUpLeg', 'mixamorig:RightLeg', 'mixamorig:RightFoot', 'mixamorig:RightToeBase')),
    'legL': lambda n: n.startswith(('mixamorig:LeftUpLeg', 'mixamorig:LeftLeg', 'mixamorig:LeftFoot', 'mixamorig:LeftToeBase')),
}
KEEP_WITH = {'armR': ('mixamorig:RightShoulder',), 'armL': ('mixamorig:LeftShoulder',),
             'legR': ('mixamorig:Hips',), 'legL': ('mixamorig:Hips',)}


def meshy_chain(i):
    acc = {k: 0.0 for k in CHAINS}
    for g in mm.data.vertices[i].groups:
        n = mnames[g.group]
        for k, bones in CHAINS.items():
            if n in bones:
                acc[k] += g.weight
    return acc


names = [g.name for g in mesh.vertex_groups]
BODY = PARTS.index('Body'); LEATHER = PARTS.index('Leather')
changed = set(); stats = {'limb_only': 0, 'limb_removed': 0, 'skirt': 0}
mw = mesh.matrix_world
for v in me.vertices:
    co = mw @ v.co
    if vpart[v.index] == BODY:
        _, i, d = kd.find(co)
        if d > 0.015:
            continue
        acc = meshy_chain(i)
        cur = {names[g.group]: g.weight for g in v.groups}
        new_w = dict(cur)
        owner = max(acc, key=acc.get)
        if acc[owner] >= 0.7:
            new_w = {n: w for n, w in cur.items() if OURS[owner](n) or n in KEEP_WITH[owner]}
            if new_w != cur:
                stats['limb_only'] += 1
        for k, s in acc.items():
            if s <= 0.05:
                stripped = {n: w for n, w in new_w.items() if not OURS[k](n)}
                if stripped != new_w:
                    stats['limb_removed'] += 1
                new_w = stripped
        if new_w != cur and sum(new_w.values()) > 1e-4:
            for g in list(v.groups):
                mesh.vertex_groups[g.group].remove([v.index])
            t = sum(new_w.values())
            for n, w in new_w.items():
                mesh.vertex_groups[n].add([v.index], w / t, 'REPLACE')
            changed.add(v.index)
    elif vpart[v.index] == LEATHER and 0.50 < co.z < 0.80:
        # skirt strips below the belt follow the pelvis, with the nearer thigh's swing
        side = 'mixamorig:LeftUpLeg' if co.x > 0 else 'mixamorig:RightUpLeg'
        w_leg = 0.0 if abs(co.x) < 0.06 else min(0.3, (abs(co.x) - 0.06) * 2.0)
        for g in list(v.groups):
            mesh.vertex_groups[g.group].remove([v.index])
        mesh.vertex_groups['mixamorig:Hips'].add([v.index], 1.0 - w_leg, 'REPLACE')
        if w_leg > 0:
            mesh.vertex_groups[side].add([v.index], w_leg, 'REPLACE')
        changed.add(v.index); stats['skirt'] += 1
for o in new:
    bpy.data.objects.remove(o, do_unlink=True)

bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.wm.save_mainfile()
print('REGION WEIGHTS', stats, 'changed', len(changed))
