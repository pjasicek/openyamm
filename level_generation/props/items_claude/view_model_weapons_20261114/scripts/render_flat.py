"""Quick look at a weapon lying along X (blaster, crossbow; README.md): side, top and three-quarter views in one sheet,
Workbench studio light (textured when the GLB has textures and no emissive image is picked).

Usage: blender --background --python render_flat.py -- <in.glb|in.blend> <out.png>
"""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
if SRC.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=SRC)
    textured = False
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    textured = True
    # Workbench shows the first image node: keep only the base colour linked.
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        for node in list(mat.node_tree.nodes):
            if node.type == 'TEX_IMAGE' and node.image is not None and 'emissive' in node.image.name.lower():
                mat.node_tree.nodes.remove(node)
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
co = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in meshes])
lo, hi = co.min(0), co.max(0)
centre = Vector(((lo + hi) / 2).tolist())
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE' if textured else 'SINGLE'
scene.display.shading.single_color = (0.62, 0.62, 0.64)
scene.display.shading.show_cavity = not textured
scene.world = bpy.data.worlds.new('w')
scene.world.color = (0.18, 0.18, 0.2)
scene.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.clip_end = 2000
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = 900, 600
size = float(np.ptp(co, 0).max()) * 1.08
paths = []
for name, d in (('side', (0, -1, 0)), ('top', (0, 0, 1)), ('quarter', (0.55, -0.7, 0.45)), ('back', (0, 1, 0))):
    cam.data.ortho_scale = size
    d = Vector(d).normalized()
    cam.location = centre + d * 500
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y' if name != 'top' else 'X').to_euler()
    p = os.path.join(os.path.dirname(OUT), f'_flat_{name}.png')
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    paths.append(p)
import subprocess
subprocess.run(['python3', '-I', '-c', f"""
from PIL import Image
ps={paths!r}
ims=[Image.open(p) for p in ps]
s=Image.new('RGB',(1800,1200))
for i,im in enumerate(ims): s.paste(im,((i%2)*900,(i//2)*600))
s.save({OUT!r})
import os
for p in ps: os.remove(p)
"""], check=True)
