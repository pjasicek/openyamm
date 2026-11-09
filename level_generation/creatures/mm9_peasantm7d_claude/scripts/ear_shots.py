"""Clay shots of the head of a master blend (rest pose), ears tinted red: front, both sides, back, top, three-quarters.
Args (Blender): <blend> <out dir> [prefix]"""
import bpy, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, outdir = a[0], a[1]; prefix = a[2] if len(a) > 2 else 'ears'
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = body.data
ear = np.zeros(len(me.polygons), np.int32)
if 'ear' in me.attributes: me.attributes['ear'].data.foreach_get('value', ear)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
me.materials.clear()
for name, col in (('body', (0.55, 0.55, 0.58, 1)), ('head', (0.8, 0.7, 0.62, 1)), ('ear', (0.9, 0.2, 0.15, 1))):
    m = bpy.data.materials.new(name); m.diffuse_color = col; me.materials.append(m)
me.polygons.foreach_set('material_index', np.where(ear > 0, 2, np.where(hd > 0, 1, 0)).tolist())
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 512
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.35, 0.35, 0.37)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 0.42
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((-0.011, 0.0, 0.80))
dirs = {'front': (0, -1, 0.05), 'side_px': (1, 0, 0.05), 'side_nx': (-1, 0, 0.05), 'back': (0, 1, 0.05),
        'top': (0, 0.2, 1), 'q34': (0.8, -1, 0.3), 'q34b': (-0.8, 1, 0.3)}
for k, d in dirs.items():
    d = Vector(d).normalized(); cam.location = c + d * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{k}.png'); bpy.ops.render.render(write_still=True)
print('SHOTS', outdir)
