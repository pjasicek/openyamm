"""Lowest vertex of a GLB's LOD0 node over every frame of one clip, with its dominant bone: blender -b -P probe_floor.py -- <glb> <node> <clip>"""
import sys, bpy, bmesh
glb, node, clip = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
o = bpy.data.objects[node]; rig = next(x for x in bpy.data.objects if x.type == 'ARMATURE'); sc = bpy.context.scene
rig.animation_data.action = bpy.data.actions[clip]; a = rig.animation_data.action
names = {g.index: g.name for g in o.vertex_groups}; res = []
for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1):
    sc.frame_set(f); b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); v = min(b.verts, key=lambda q: q.co.z); res.append((v.co.z, f, v.index, tuple(v.co))); b.free()
for z, f, i, co in sorted(res)[:6]:
    gs = sorted(o.data.vertices[i].groups, key=lambda g: -g.weight)[:2]
    print('MIN', round(z * 1000, 2), 'mm frame', f, 'vertex', i, [(names[g.group], round(g.weight, 2)) for g in gs], [round(c, 3) for c in co])
