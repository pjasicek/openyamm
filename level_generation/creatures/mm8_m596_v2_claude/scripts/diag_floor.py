"""Lowest skinned vertices of a clip frame with their weights. Usage: blender -b -P diag_floor.py -- <blend> <clip> <frame>"""
import os, sys, bpy
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
rig = bpy.data.objects['CrystalRig']; body = bpy.data.objects['CrystalWalker']
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
def low():
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    r = sorted(((body.matrix_world @ v.co).z, v.index) for v in m.vertices)[:5]; ev.to_mesh_clear(); return r
print('REST', low(), 'mesh min', min(v.co.z for v in body.data.vertices), 'body parent', body.parent, body.matrix_world.translation, rig.matrix_world.translation)
rig.animation_data.action = bpy.data.actions[a[1]]; bpy.context.scene.frame_set(int(a[2]))
r = low(); print('POSE', r)
names = {g.index: g.name for g in body.vertex_groups}
for z, i in r[:3]:
    print(i, round(z, 4), body.data.vertices[i].co[:], [(names[g.group], round(g.weight, 3)) for g in body.data.vertices[i].groups])
