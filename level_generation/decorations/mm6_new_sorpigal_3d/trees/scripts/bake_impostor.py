"""Impostor capture of LOD0 (work/<id>/tree.blend -> impostor_albedo_raw.png, impostor_normal_raw.png). Usage: -- <id>.
Cycles, orthographic camera on -Y looking +Y, square frame S = 1.02 x tree height with the bottom edge on the ground,
512 px, transparent film, Raw view transform (pixel = shader value). Every material is swapped for an emission:
 - albedo: base colour texel x the COLOR_0 canopy occlusion ('Color' attribute), exactly what the engine shades on
   the 3D levels (base colour x vertex colour); leaves alpha-clipped at 0.5 as in the engine.
 - normal: the shading normal (custom crown normals + normal map) in camera space, encoded 0.5 + 0.5 n. For the
   impostor quad (x right, y up, z toward the viewer) this is directly its tangent-space normal map.
The impostor quad (impostor.json: size S) is added by export_tree.py."""
import bpy, os, json
from mathutils import Vector
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
WORK = spec['work']
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tree.blend'))
sc = bpy.context.scene
tree = bpy.data.objects['Tree']
for o in bpy.data.objects:
    o.hide_render = o is not tree
H = max((tree.matrix_world @ Vector(c)).z for c in tree.bound_box)
S = H * 1.02
sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = False
if spec.get('transparent_bounces'):
    # many overlapping cutout cards (large cards, dense crowns) exceed Cycles' default transparent bounces and
    # render black where the ray gives up; species opt in to a higher limit (absent = the approved renders)
    sc.cycles.transparent_max_bounces = spec['transparent_bounces']
sc.render.film_transparent = True; sc.view_settings.view_transform = 'Raw'
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '16'
cam = bpy.data.objects.new('ImpostorCam', bpy.data.cameras.new('ImpostorCam')); sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = S
cam.location = (0, -40, S / 2); cam.rotation_euler = (1.5707963, 0, 0)
cam.data.clip_end = 100
sc.world = sc.world or bpy.data.worlds.new('W')


def emission_tree(mat, mode):
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    tex = bsdf.inputs['Base Color'].links[0].from_node
    nmap = bsdf.inputs['Normal'].links[0].from_node
    em = nt.nodes.new('ShaderNodeEmission')
    if mode == 'albedo':
        # linear texel x linear occlusion; the albedo pass renders with the Standard (sRGB) view transform
        attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
        mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
        nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
        nt.links.new(mul.outputs[0], em.inputs['Color'])
    else:
        vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'
        vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
        nt.links.new(nmap.outputs['Normal'], vt.inputs[0])
        enc = nt.nodes.new('ShaderNodeVectorMath'); enc.operation = 'MULTIPLY_ADD'
        nt.links.new(vt.outputs[0], enc.inputs[0]); enc.inputs[1].default_value = (0.5, 0.5, -0.5)
        enc.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(enc.outputs[0], em.inputs['Color'])
    surface = em.outputs[0]
    if bsdf.inputs['Alpha'].links:
        clip = bsdf.inputs['Alpha'].links[0].from_node
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(clip.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(em.outputs[0], mx.inputs[2]); surface = mx.outputs[0]
    nt.links.new(surface, out.inputs['Surface'])


for mode in ('albedo', 'normal'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tree.blend')) if mode == 'normal' else None
    if mode == 'normal':
        sc = bpy.context.scene; tree = bpy.data.objects['Tree']
        for o in bpy.data.objects:
            o.hide_render = o is not tree
        sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = False
        sc.render.film_transparent = True; sc.view_settings.view_transform = 'Raw'
        sc.render.resolution_x = sc.render.resolution_y = 1024
        sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
        sc.render.image_settings.color_depth = '16'
        cam = bpy.data.objects.new('ImpostorCam', bpy.data.cameras.new('ImpostorCam')); sc.collection.objects.link(cam)
        sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = S
        cam.location = (0, -40, S / 2); cam.rotation_euler = (1.5707963, 0, 0); cam.data.clip_end = 100
    for m in tree.data.materials:
        emission_tree(m, mode)
    sc.view_settings.view_transform = 'Standard' if mode == 'albedo' else 'Raw'
    sc.view_settings.look = 'None'; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    sc.render.filepath = os.path.join(WORK, f'impostor_{mode}_raw.png')
    bpy.ops.render.render(write_still=True)
    print('IMPOSTOR', mode, sc.render.filepath)
json.dump({'size_m': S, 'tree_height_m': H}, open(os.path.join(WORK, 'impostor.json'), 'w'))
print('IMPOSTOR size', round(S, 3))
