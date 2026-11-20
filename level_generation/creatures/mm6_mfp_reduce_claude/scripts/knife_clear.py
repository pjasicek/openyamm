"""G6 for the cutpurse Attack: knife vertices inside the posed body (nearest body point within 4 cm and behind its
surface normal), every frame; also the right hand's fingers inside the torso/thighs. Args: -- <blend> <action>"""
import bpy, sys, bmesh
from mathutils.bvhtree import BVHTree
blend, an = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; knife = bpy.data.objects['KnifeAsset']
act = bpy.data.actions[an]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
worst = []
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new(); bm.from_object(body, dg); bm.transform(body.matrix_world); bm.normal_update(); tree = BVHTree.FromBMesh(bm)
    km = knife.evaluated_get(dg).to_mesh(); M = knife.matrix_world
    inside = 0; deepest = 0
    for v in km.vertices:
        p = M @ v.co; loc, nrm, idx, d = tree.find_nearest(p)
        if loc is not None and d < 0.04 and (p - loc).dot(nrm) < 0:
            inside += 1; deepest = max(deepest, d)
    knife.evaluated_get(dg).to_mesh_clear(); bm.free()
    if inside: worst.append((f, inside, round(deepest * 1000, 1)))
print('KNIFE', an, 'frames with knife inside the body:', len(worst), worst[:20])
