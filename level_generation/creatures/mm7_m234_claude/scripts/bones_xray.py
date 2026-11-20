"""X-ray of the rig's bones whose names start with one of the given prefixes, drawn as rods over the rest mesh
(workbench, X-ray shading), front/side/back/top views to review/bones_<tag>_<view>.png.
Args: -- <blend> <tag> <prefix> [prefix ...]"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, prefixes = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bm = bmesh.new()
for b in rig.data.bones:
    if not any(b.name.startswith(p) for p in prefixes):
        continue
    h, t = rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local
    v = t - h
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.015, radius2=0.008, depth=v.length)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((h + t) / 2) @ v.to_track_quat('Z', 'Y').to_matrix().to_4x4(), verts=r['verts'])
    s = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.022)
    bmesh.ops.translate(bm, verts=s['verts'], vec=h)
me = bpy.data.meshes.new('bones'); bm.to_mesh(me); ob = bpy.data.objects.new('bones', me); bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('red'); mat.diffuse_color = (1, 0.1, 0.1, 1); me.materials.append(mat)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.show_xray = True; sh.xray_alpha = 0.35; sh.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1000, 700
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.1
for name, dv in (('front', (0, 1, 0)), ('side', (-1, 0, 0)), ('back', (0, -1, 0)), ('top', (0, 0.01, -1))):
    dv = Vector(dv).normalized(); cam.location = Vector((0, 0, 1.0)) - dv * 6
    cam.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', f'bones_{tag}_{name}.png'); bpy.ops.render.render(write_still=True)
