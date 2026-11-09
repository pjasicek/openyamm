"""Fre (2026-11-04 pass 2): find thin paint lines on the head in screen space and map them back to texels. Renders the rest-pose GLB
(EEVEE, no lighting: pure emission) twice per view: the base colour, and the UV (R = u, G = v, B = 1 on the head material, 0 elsewhere)
into float EXR/PNG16. Args: <glb> <outdir> <views comma> [size] [ortho] [centre x,y,z]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, views = a[0], a[1], a[2].split(','); size = int(a[3]) if len(a) > 3 else 1024; ortho = float(a[4]) if len(a) > 4 else 0.26
cen = Vector([float(x) for x in (a[5] if len(a) > 5 else '0,0,0.60').split(',')])
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
if arm:
    if arm.animation_data: arm.animation_data.action = None
    for pb in arm.pose.bones: pb.matrix_basis.identity()
for o in sc.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
try: sc.render.filter_size = 0.0      # exact UVs per pixel (no film filter blending across seams)
except Exception: pass
sc.render.resolution_x = sc.render.resolution_y = size; sc.render.film_transparent = True
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0, 0, 0)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
DIR = {'front': (0, -1, 0.0), 'q34': (-1, -1.2, 0.2), 'q34l': (1, -1.2, 0.2), 'left': (1, 0, 0), 'right': (-1, 0, 0), 'low': (-0.5, -0.8, -0.7), 'lowf': (0, -0.7, -0.9)}
mats = {m.name: m for m in bpy.data.materials}
orig = {}
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree; img = next((n.image for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'base' in n.label.lower() + n.name.lower() + n.image.name.lower()), None)
    if img is None:
        bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf and bsdf.inputs['Base Color'].links: img = bsdf.inputs['Base Color'].links[0].from_node.image
    orig[m.name] = img
def setup(mode):
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        nt = m.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); nt.links.new(e.outputs[0], o.inputs[0])
        if mode == 'base' and orig.get(m.name) is not None:
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = orig[m.name]; t.interpolation = 'Closest'; nt.links.new(t.outputs[0], e.inputs[0])
        elif mode == 'pos':
            gm = nt.nodes.new('ShaderNodeNewGeometry'); nt.links.new(gm.outputs['Position'], e.inputs[0])
        elif mode == 'uv':
            tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); com = nt.nodes.new('ShaderNodeCombineXYZ')
            nt.links.new(tc.outputs['UV'], sep.inputs[0]); nt.links.new(sep.outputs[0], com.inputs[0]); nt.links.new(sep.outputs[1], com.inputs[1])
            com.inputs[2].default_value = 1.0 if 'Head' in m.name else 0.0
            nt.links.new(com.outputs[0], e.inputs[0])
        m.blend_method = 'OPAQUE' if hasattr(m, 'blend_method') else None
for mode in (('base', 'uv', 'pos') if __import__('os').environ.get('POSMODE') else ('base', 'uv')):
    setup(mode)
    if mode in ('uv', 'pos'):
        sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
    else:
        sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
    for v in views:
        d = Vector(DIR[v]).normalized(); cam.location = cen + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{mode}_{v}' + ('.exr' if mode in ('uv', 'pos') else '.png')); bpy.ops.render.render(write_still=True)
print('UVPROBE', out)
