"""Debug renders of 'Body' coloured by its face attribute 'part' (0 body grey, 1 head blue, 2 pieces yellow, 3 loft
red) with edges drawn as a wireframe modifier. Args: blend outdir views(comma) size ortho cx,cy,cz"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)
b = bpy.data.objects['Body']; me = b.data
cols = [(0.7, 0.7, 0.7, 1), (0.3, 0.45, 1, 1), (1, 0.9, 0.2, 1), (1, 0.25, 0.2, 1)]
me.materials.clear()
for i, c in enumerate(cols):
    m = bpy.data.materials.new(f'p{i}'); m.diffuse_color = c; me.materials.append(m)
part = me.attributes.get('part')
for p in me.polygons:
    p.material_index = part.data[p.index].value if part else 0
w = bpy.data.objects.new('wire', me.copy()); sc.collection.objects.link(w)
w.matrix_world = b.matrix_world
wm = w.modifiers.new('w', 'WIREFRAME'); wm.thickness = 0.0006; wm.use_replace = True
blk = bpy.data.materials.new('k'); blk.diffuse_color = (0, 0, 0, 1)
w.data.materials.clear(); w.data.materials.append(blk)
for p in w.data.polygons:
    p.material_index = 0
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = int(a[3])
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[4])
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[5].split(',')])
dirs = {'q34': (-1, -1.25, 0.55), 'front': (0, -1, 0.05), 'left': (1, 0, 0.05), 'below': (0, -0.6, -1), 'back': (0, 1, 0.1)}
os.makedirs(a[1], exist_ok=True)
for v in a[2].split(','):
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(a[1], f'part_{v}.png')
    bpy.ops.render.render(write_still=True)
print('PARTS done')
