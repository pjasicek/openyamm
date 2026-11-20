"""Rest-pose renders of the source with faces coloured by a per-face label array (<labels>.npy, same order as
dump_mesh.py) from front, back and left -> review/labels_<name>.png. Usage: blender -b -P label_views.py -- <labels.npy> <name>"""
import os, sys, bpy, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; lab = np.load(os.path.join(HERE, a[0])).astype(int)
if lab.dtype == bool or lab.max() <= 1:
    lab = lab.astype(int)
cols = [(.55, .55, .55), (.9, .2, .2), (.2, .8, .2), (.2, .3, .95), (.95, .8, .1), (.8, .2, .9), (.1, .85, .85), (1, .5, .1), (.4, .2, .1)]
o.data.materials.clear()
for k, col in enumerate(cols):
    m = bpy.data.materials.new(f'L{k}'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*col, 1); o.data.materials.append(m)
me = o.data; me.calc_loop_triangles()
tri_poly = np.array([t.polygon_index for t in me.loop_triangles])
pl = np.zeros(len(me.polygons), int); pl[tri_poly] = lab
for p in me.polygons:
    p.material_index = int(pl[p.index]) % len(cols)
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob is not o: ob.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = 500; sc.render.resolution_y = 700
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.3, .3, .32, 1)
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sun.data.energy = 3; sc.collection.objects.link(sun); sun.rotation_euler = (.8, 0, .4)
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('LV_SCALE', 1.9)); c = Vector([float(x) for x in os.environ.get('LV_CENTER', '0,0,0.85').split(',')])
for nm, d in (('front', Vector((0, -1, 0))), ('back', Vector((0, 1, 0))), ('left', Vector((1, 0, 0)))):
    cam.location = c + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    fp = os.path.join(HERE, 'work', f'_lv_{nm}.png'); sc.render.filepath = fp; bpy.ops.render.render(write_still=True)
import subprocess
subprocess.run(['python3', '-c', 'import sys; from PIL import Image; ims=[Image.open(f) for f in sys.argv[2:]]; o=Image.new("RGB",(sum(i.width for i in ims),ims[0].height)); [o.paste(im,(k*ims[0].width,0)) for k,im in enumerate(ims)]; o.save(sys.argv[1])',
                os.path.join(HERE, 'review', f'labels_{a[1]}.png')] + [os.path.join(HERE, 'work', f'_lv_{n}.png') for n in ('front', 'back', 'left')], check=True)
