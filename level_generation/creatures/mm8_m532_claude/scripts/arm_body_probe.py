"""Left-arm vertices (upper arm beyond 14 cm from the shoulder joint, forearm, hand, fingers) inside the rest of the body (every face not on the left arm,
the bow or its string), per frame: count and depth. Usage: blender -b -P arm_body_probe.py -- <blend> <action> <frames,comma|all>"""
import bpy, bmesh, sys
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
act = bpy.data.actions[a[1]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
names = [g.name for g in body.vertex_groups]
dom = [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in body.data.vertices]
LEFT = lambda n: n.startswith('L') and n[1:2].isupper() and not n.startswith('Leg')
arm = [i for i, n in enumerate(dom) if LEFT(n) and n != 'LShoulder']
skip = lambda n: LEFT(n) or n in ('Bow', 'StringNock', 'StringTop', 'StringBottom', 'Arrow', 'LShoulder')
faces = [p.index for p in body.data.polygons if not any(skip(dom[i]) for i in p.vertices)]
f0, f1 = (int(x) for x in act.frame_range)
frames = range(f0, f1 + 1) if a[2] == 'all' else [int(x) for x in a[2].split(',')]
worst = (0, None, 0)
for f in frames:
    sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = [body.matrix_world @ v.co for v in me.vertices]; bm = bmesh.new(); vs = [bm.verts.new(c) for c in co]
    for fi in faces:
        try:
            bm.faces.new([vs[i] for i in me.polygons[fi].vertices])
        except ValueError:
            pass
    bm.normal_update(); tree = BVHTree.FromBMesh(bm); n = 0; deep = 0.; who = ''
    sh = rig.pose.bones['LArm'].head
    for i in arm:
        if (co[i] - sh).length < .14:                                # armpit and deltoid squeeze: not counted
            continue
        hit = tree.find_nearest(co[i], .1)
        if hit[0] is not None:
            s = (co[i] - hit[0]).dot(hit[1])
            if s < -.004:
                n += 1
                if -s > deep:
                    face = me.polygons[faces[hit[2]]] if hit[2] < len(faces) else None
                    deep = -s; who = (dom[i], dom[face.vertices[0]] if face else '', [round(x, 2) for x in co[i] - sh])
    bm.free(); ev.to_mesh_clear()
    if deep * 1000 > worst[2]:
        worst = (f, who, round(deep * 1000, 1))
    if a[2] != 'all':
        print('ARMBODY', a[1], f, 'verts', n, 'depth_mm', round(deep * 1000, 1), who)
print('ARMBODY_WORST', a[1], worst)
