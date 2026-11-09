"""Impostor capture of LOD0 (work/<id>/plant.blend -> impostor_albedo_raw.png, impostor_normal_raw.png,
impostor.json), as the trees do: Cycles, orthographic camera on -Y looking +Y, frame width 2 x the plant's largest
horizontal reach (so any yaw fits), height = plant height, bottom edge on the ground; every material becomes an
emission of base colour texel x COLOR_0 (albedo; alpha clipped at 0.5) or of the camera-space shading normal
encoded 0.5 + 0.5 n (normal, which is the billboard quad's tangent-space normal). Usage: -- <id>"""
import bpy, json, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as dc
SID = sys.argv[sys.argv.index('--') + 1]
WORK = dc.work(SID)
MAX_RES = 1024


def setup():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'plant.blend'))
    sc = bpy.context.scene; plant = bpy.data.objects['Plant']
    for o in bpy.data.objects:
        o.hide_render = o is not plant
    me = plant.data
    reach = max(math.hypot(v.co.x, v.co.y) for v in me.vertices) * 1.02
    height = max(v.co.z for v in me.vertices) * 1.01
    w, h = 2 * reach, height
    if w >= h:
        rx, ry = MAX_RES, max(8, int(round(MAX_RES * h / w / 4)) * 4)
    else:
        rx, ry = max(8, int(round(MAX_RES * w / h / 4)) * 4), MAX_RES
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.use_denoising = False
    sc.cycles.transparent_max_bounces = 128     # dense spray cards: the default 8 leaves opaque black texels
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    cam = bpy.data.objects.new('ImpostorCam', bpy.data.cameras.new('ImpostorCam')); sc.collection.objects.link(cam)
    sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(w, h)
    scale = max(w, h)
    w, h = scale * rx / max(rx, ry), scale * ry / max(rx, ry)      # the frame actually rendered
    cam.location = (0, -40, h / 2); cam.rotation_euler = (math.pi / 2, 0, 0); cam.data.clip_end = 100
    sc.world = sc.world or bpy.data.worlds.new('W')
    return sc, plant, w, h


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
        # double-sided leaves are shaded with the normal turned toward the viewer: keep z pointing at the camera
        # (Blender camera space looks down -z, encoded below as +z) so no texel is lit from behind
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(vt.outputs[0], sep.inputs[0])
        neg = nt.nodes.new('ShaderNodeMath'); neg.operation = 'MINIMUM'; neg.inputs[1].default_value = 0.0
        nt.links.new(sep.outputs['Z'], neg.inputs[0])
        com = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(sep.outputs['X'], com.inputs['X']); nt.links.new(sep.outputs['Y'], com.inputs['Y'])
        nt.links.new(neg.outputs[0], com.inputs['Z'])
        enc = nt.nodes.new('ShaderNodeVectorMath'); enc.operation = 'MULTIPLY_ADD'
        nt.links.new(com.outputs[0], enc.inputs[0]); enc.inputs[1].default_value = (0.5, 0.5, -0.5)
        enc.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(enc.outputs[0], em.inputs['Color'])
    surface = em.outputs[0]
    if bsdf.inputs['Alpha'].links:
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tex.outputs['Alpha'], clip.inputs[0])
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(clip.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(em.outputs[0], mx.inputs[2]); surface = mx.outputs[0]
    nt.links.new(surface, out.inputs['Surface'])


for mode in ('albedo', 'normal'):
    sc, plant, w, h = setup()
    for m in plant.data.materials:
        emission(m, mode)
    sc.view_settings.view_transform = 'Standard' if mode == 'albedo' else 'Raw'
    sc.view_settings.look = 'None'; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    sc.render.filepath = os.path.join(WORK, f'impostor_{mode}_raw.png')
    bpy.ops.render.render(write_still=True)
    print('IMPOSTOR', mode, sc.render.filepath)
json.dump({'width_m': w, 'height_m': h}, open(os.path.join(WORK, 'impostor.json'), 'w'))
