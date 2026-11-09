"""Debug render: reduced candidate head with ivory regions (work/ivory_faces.npz) in distinct colours, ids drawn at
their projected centres. Views: side (+x), top, back, front. Out: review/horns/regions_<view>.png"""
import os, math, colorsys, json
import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('RR_BLEND', 'ladder.blend')))
o = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]; rig = bpy.data.objects['Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
for x in bpy.data.objects:
    x.hide_render = x not in (o,)
me = o.data
if os.environ.get('RR_ATTR'):
    region = np.zeros(len(me.polygons), np.int32); me.attributes[os.environ['RR_ATTR']].data.foreach_get('value', region)
    region[region == 0] = -1
else:
    region = np.load(os.path.join(HERE, 'work', os.environ.get('RR_REGIONS', 'ivory_faces.npz')))['region']; me.materials.clear()
skin = bpy.data.materials.new('skin'); skin.diffuse_color = (.55, .3, .25, 1); skin.use_nodes = True
skin.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.55, .3, .25, 1); me.materials.append(skin)
ids = sorted(set(region.tolist()) - {-1})
for k, r in enumerate(ids):
    m = bpy.data.materials.new(f'r{r}'); m.use_nodes = True
    c = colorsys.hsv_to_rgb((k * .618) % 1, .9, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*c, 1); me.materials.append(m)
slot = {r: k + 1 for k, r in enumerate(ids)}
for f in me.polygons:
    f.material_index = slot.get(int(region[f.index]), 0)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 900
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.4, .4, .45, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(40), 0, math.radians(-25))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('RR_SCALE', '.6'))
c = Vector(json.loads(os.environ.get('RR_CENTER', '[0, -1.27, 1.0]')))
centres = {}
fc = np.array([f.center[:] for f in me.polygons])
for r in ids:
    centres[r] = fc[region == r].mean(0)
out = os.path.join(HERE, 'review', 'horns'); os.makedirs(out, exist_ok=True); labels = {}
tag = os.environ.get('RR_TAG', 'regions')
for view, d in {'side': (1, 0, 0), 'top': (0, 0, 1), 'back': (0, 1, .3), 'front': (0, -1, .2), 'q34': (.8, -.6, .5)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(out, f'{tag}_{view}.png'); bpy.ops.render.render(write_still=True)
    labels[view] = {int(r): list(world_to_camera_view(sc, cam, Vector(p)))[:2] for r, p in centres.items()}
json.dump(labels, open(os.path.join(out, f'{tag}_labels.json'), 'w'))
