"""Workbench preview of work/textured_master.blend with given base-colour images per domain (body, head, wings).
Usage: preview_textured.py -- <outdir> <body.png> <head.png> <wings.png> clip:frame:view:scale[:tx,ty,tz] ... (clip "rest" = bind pose)"""
import bpy, sys
from pathlib import Path
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/textured_master.blend')); out = Path(a[0]); out.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for slot, path in enumerate(a[1:4]):
    mat = body.data.materials[slot]; mat.use_nodes = True; nt = mat.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(Path(path).resolve()))
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat.use_backface_culling = False
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = 1000; sc.render.resolution_y = 800; sc.render.resolution_percentage = 100
cam = bpy.data.objects.new('PrevCam', bpy.data.cameras.new('PrevCam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
dirs = {'front': (0, -1, .08), 'side': (1, -.2, .12), 'left': (1, 0, .05), 'right': (-1, 0, .05), 'quarter': (1, -1, .45), 'rear': (-.8, 1, .4), 'top': (0, -.05, 1), 'low': (.7, -1, -.35), 'under': (0, -.3, -1)}
for spec in a[4:]:
    p = spec.split(':'); clip, frame, view, scale = p[0], int(p[1]), p[2], float(p[3])
    rig.animation_data_create()
    if clip == 'rest':
        rig.animation_data.action = None
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        bpy.context.view_layer.update()
    else:
        rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(frame)
    target = Vector(tuple(float(v) for v in p[4].split(','))) if len(p) > 4 else Vector((0, -.05, .26))
    cam.location = target + Vector(dirs[view]).normalized() * 3; cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = scale
    sc.render.filepath = str(out / f'{clip}_{frame:02d}_{view}_{scale}.png'); bpy.ops.render.render(write_still=True)
