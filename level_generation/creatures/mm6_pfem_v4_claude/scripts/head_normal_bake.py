"""Re-bake the grafted head's normal map for its smooth shading (user review 2026-10-30: "gray smudges on the head",
"skin feels like clay"). Meshy's head model is flat shaded and its normal map was baked against those flat face
normals; the graft welds and smooths the head, so the old map added its corrections on top of already smooth normals
and blotched the face. Cycles bakes the original (flat normals + Meshy's map, placed by work/graft.json head_matrix)
onto the grafted head (smooth, decimated) in tangent space, selected to active, into the head's own layout 'HeadUV'.
Run after graft_head_parts.py on work/st_v1_parts.blend; writes work/head_normal_rebake.png (2048). Args: none"""
import bpy, os, sys, json
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
G = json.load(open(os.path.join(common.WORK, 'graft.json')))
P = json.load(open(os.path.join(common.PROJECT, 'graft.json')))
N = 2048
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
target = bpy.data.objects[f"P{G['head']:02d}"]
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, P.get('head_glb', 'meshy/head_v1/model_urls_glb.glb')))
src = max((o for o in bpy.data.objects if o not in before and o.type == 'MESH'), key=lambda o: len(o.data.vertices))
for o in [o for o in bpy.data.objects if o not in before and o is not src]:
    bpy.data.objects.remove(o, do_unlink=True)
src.parent = None
for o in bpy.context.view_layer.objects:
    o.select_set(o is src)
bpy.context.view_layer.objects.active = src
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
src.matrix_world = Matrix(G['head_matrix'])
src_uv = src.data.uv_layers.active.name
mat = bpy.data.materials.new('src_normal'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
img = bpy.data.images.load(os.path.join(common.PROJECT, 'meshy', 'head_v1', 'texture_urls_0_normal.png'))
img.colorspace_settings.name = 'Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = src_uv
nm = nt.nodes.new('ShaderNodeNormalMap'); nm.uv_map = src_uv
nt.links.new(uvn.outputs['UV'], tex.inputs['Vector']); nt.links.new(tex.outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
src.data.materials.clear(); src.data.materials.append(mat)
out = bpy.data.images.new('rebake', N, N); out.colorspace_settings.name = 'Non-Color'
tmat = bpy.data.materials.new('target'); tmat.use_nodes = True
tn = tmat.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = out; tmat.node_tree.nodes.active = tn
target.data.materials.clear(); target.data.materials.append(tmat)
target.data.uv_layers.active = target.data.uv_layers['HeadUV']
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'
bk = sc.render.bake
bk.use_selected_to_active = True; bk.cage_extrusion = 0.006; bk.max_ray_distance = 0.02; bk.margin = 8
bk.normal_space = 'TANGENT'
for o in bpy.context.view_layer.objects:
    o.select_set(o in (src, target))
bpy.context.view_layer.objects.active = target
bpy.ops.object.bake(type='NORMAL', uv_layer='HeadUV')
out.filepath_raw = os.path.join(common.WORK, 'head_normal_rebake.png'); out.file_format = 'PNG'; out.save()
print('NORMALBAKE head', target.name, 'faces', len(target.data.polygons), '->', out.filepath_raw)
