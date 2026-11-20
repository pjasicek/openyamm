"""Close-ups of both hands of the cleric master (rest pose or a clip frame), workbench clay with cavity + textured.
Args: -- <blend> <out prefix> [Action frame]"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out = a[1]
sc = bpy.context.scene; rig = bpy.data.objects['Cleric_Rig']
if len(a) > 3:
    rig.animation_data.action = bpy.data.actions[a[2]]; sc.frame_set(int(a[3]))
else:
    rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
if 'HandL' in bpy.data.objects:   # new hands present: hide the old hand faces (export_runtime removes them)
    import bmesh
    m = bpy.data.objects['Cleric']; names = {g.index: g.name for g in m.vertex_groups}
    hw = [sum(g.weight for g in v.groups if names[g.group] in ('LeftHand', 'RightHand')) for v in m.data.vertices]
    bm = bmesh.new(); bm.from_mesh(m.data)
    if 'old_hand' in m.data.attributes:
        oh = [0] * len(m.data.polygons); m.data.attributes['old_hand'].data.foreach_get('value', oh)
    else:
        oh = [sum(hw[i] for i in p.vertices) / len(p.vertices) > .5 for p in m.data.polygons]
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if oh[f.index]], context='FACES')
    bm.to_mesh(m.data); bm.free(); bpy.context.view_layer.update()
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 400
cam = bpy.data.objects.new('HC', bpy.data.cameras.new('HC')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.32
for side in ('Left', 'Right'):
    pb = rig.pose.bones[side + 'Hand']; c = rig.matrix_world @ (pb.head + (pb.matrix.to_3x3() @ Vector((0, 0.06, 0))))
    c = rig.matrix_world @ pb.head; c = c + Vector((0, 0, -0.07))
    for view, d in (('front', (0, -1, 0)), ('out', (1 if side == 'Left' else -1, 0, 0)), ('back', (0, 1, 0)), ('in', (-1 if side == 'Left' else 1, 0, .0)), ('below', (0, -0.3, -1))):
        dv = Vector(d).normalized(); cam.location = c + dv * 2
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for ct in ('MATERIAL', 'TEXTURE'):
            sc.display.shading.color_type = ct
            sc.render.filepath = f'{out}_{side}_{view}_{ct[0]}.png'; bpy.ops.render.render(write_still=True)
print('HANDS done')
