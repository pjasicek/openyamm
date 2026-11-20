"""Impostor capture of LOD0 (work/dead_<id>/tree.blend -> impostor_albedo_raw.png, impostor_normal_raw.png), as the
living trees' bake_impostor.py: Cycles, orthographic camera on -Y looking +Y, square frame S = 1.02 x the larger of
the model's height and width with the bottom edge on the ground, 1024 px, transparent film. Every material becomes an
emission: albedo = base colour texel x COLOR_0 (what the engine shades on the 3D levels), normal = the shading normal
in camera space (0.5 + 0.5 n), i.e. the impostor quad's tangent-space normal map. Twigs alpha-clipped at 0.5;
the transparent bounce limit is raised (deep card stacks otherwise render black).
Usage: blender --background --python dead_impostor.py -- <id>"""
import bpy, os, sys, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dead_common as dc
spec = dc.load(); WORK = spec['work']


def setup():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tree.blend'))
    sc = bpy.context.scene; tree = bpy.data.objects['Tree']
    for o in bpy.data.objects:
        o.hide_render = o is not tree
    corners = [tree.matrix_world @ Vector(c) for c in tree.bound_box]
    h = max(c.z for c in corners); w = 2 * max(max(abs(c.x) for c in corners), max(abs(c.y) for c in corners))
    S = max(h, w) * 1.02
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = False
    # many overlapping twig cards: the default transparent bounce limit turns deep stacks black
    sc.cycles.transparent_max_bounces = 128; sc.cycles.max_bounces = 128
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '16'
    cam = bpy.data.objects.new('ImpostorCam', bpy.data.cameras.new('ImpostorCam')); sc.collection.objects.link(cam)
    sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = S
    cam.location = (0, -40, S / 2); cam.rotation_euler = (1.5707963, 0, 0); cam.data.clip_end = 100
    sc.world = sc.world or bpy.data.worlds.new('W')
    return sc, tree, S, h


def emission(mat, mode):
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    tex = bsdf.inputs['Base Color'].links[0].from_node
    nmap = bsdf.inputs['Normal'].links[0].from_node
    em = nt.nodes.new('ShaderNodeEmission')
    if mode == 'albedo':
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
    sc, tree, S, h = setup()
    for m in {m for m in tree.data.materials}:
        emission(m, mode)
    sc.view_settings.view_transform = 'Standard' if mode == 'albedo' else 'Raw'
    sc.view_settings.look = 'None'; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    sc.render.filepath = os.path.join(WORK, f'impostor_{mode}_raw.png')
    bpy.ops.render.render(write_still=True)
    print('IMPOSTOR', mode, sc.render.filepath)
json.dump({'size_m': S, 'tree_height_m': h}, open(os.path.join(WORK, 'impostor.json'), 'w'))
print('IMPOSTOR size', round(S, 3))
