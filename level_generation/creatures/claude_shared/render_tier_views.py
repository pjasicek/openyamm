"""Render a rest-pose creature with several base-colour textures (for example tier_textures.py output before and
after a change), front and three-quarter, Workbench studio light on a dark background, into one row per texture.
Usage: blender --background <blend> --python render_tier_views.py -- <mesh object> <out.png> <distance> <target_z>
       <ortho_scale> <texture.png> [texture.png ...]
The mesh faces -Y (creature front). Labels are the texture file stems."""
import bpy, sys, os, subprocess
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index('--') + 1:]
mesh_name, out, dist, tz, scale = args[0], args[1], float(args[2]), float(args[3]), float(args[4])
textures = args[5:]
mesh = bpy.data.objects[mesh_name]
for rig in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o is not mesh
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False; sh.show_shadows = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.16, 0.17, 0.18)
sc.render.resolution_x = sc.render.resolution_y = 380
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = scale
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
mat = bpy.data.materials.new('preview'); mat.use_nodes = True; nt = mat.node_tree
node = nt.nodes.new('ShaderNodeTexImage')
nt.links.new(node.outputs['Color'], next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for p in mesh.data.polygons:
    p.material_index = 0
tmp = os.path.splitext(out)[0] + '_cells'; os.makedirs(tmp, exist_ok=True)
cells = []
for t in textures:
    node.image = bpy.data.images.load(t)
    for view, loc in (('front', (0, -dist, tz + dist * 0.12)), ('q', (dist * 0.7, -dist * 0.7, tz + dist * 0.12))):
        target = Vector((0, 0, tz)); d = (target - Vector(loc)).normalized()
        cam.matrix_world = Matrix.Translation(Vector(loc)) @ d.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
        p = os.path.join(tmp, f'{os.path.splitext(os.path.basename(t))[0]}_{view}.png')
        sc.render.filepath = p; bpy.ops.render.render(write_still=True); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys, os
from PIL import Image, ImageDraw
out, paths = sys.argv[1], sys.argv[2:]
rows = [paths[i:i + 2] for i in range(0, len(paths), 2)]
o = Image.new('RGB', (760, 396 * len(rows)), (20, 20, 20)); d = ImageDraw.Draw(o)
for r, pair in enumerate(rows):
    for c, p in enumerate(pair):
        o.paste(Image.open(p), (c * 380, r * 396 + 16))
    d.text((4, r * 396 + 2), os.path.basename(pair[0]).rsplit('_', 1)[0], fill=(255, 220, 120))
o.save(out)
""", out] + cells, check=True)
print('RENDERED', out)
