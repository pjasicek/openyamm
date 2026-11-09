"""Clay close-ups of a blend's 'Body' or a GLB's first mesh. Args: file outdir name:cx,cy,cz:dx,dy,dz:ortho ... (env FLAT=1 for flat shading, WIRE=1 overlay)"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
f, out = argv[0], argv[1]; shots = argv[2:]
os.makedirs(out, exist_ok=True)
if f.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=f)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=f)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH':
        o.data.materials.clear()
        if not os.environ.get('FLAT'):
            o.data.shade_smooth() if hasattr(o.data, 'shade_smooth') else None
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.72, 0.68, 0.6); sh.show_backface_culling = True
if os.environ.get('WIRE'):
    sh.show_object_outline = False
    for o in sc.objects:
        if o.type == 'MESH':
            m = o.modifiers.new('w', 'WIREFRAME'); m.thickness = float(os.environ['WIRE']); m.use_replace = False; m.use_even_offset = False
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('SIZE', '700'))
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.3); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_end = 100
for s in shots:
    n, c, d, o = s.split(':')
    c = Vector([float(x) for x in c.split(',')]); d = Vector([float(x) for x in d.split(',')]).normalized()
    cd.ortho_scale = float(o); cam.location = c + d * 8
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}/{n}.png'; bpy.ops.render.render(write_still=True)
print('CLAY DONE')
