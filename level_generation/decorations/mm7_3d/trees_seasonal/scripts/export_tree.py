"""work/<id>/tree.blend + impostor maps -> tree_export.glb (Tree, Tree_LOD1, Tree_LOD2, Tree_LOD3). Usage: -- <id>.
Tree_LOD3 is one quad in Blender's XZ plane (glTF XY), x -S/2..S/2, z 0..S, facing -Y (glTF +Z), material Impostor.
Material custom properties go to glTF extras; the 'Color' point attribute (canopy occlusion; white on the quad)
is exported as COLOR_0. post_process.py fixes alpha modes and links the LODs."""
import bpy, bmesh, os, json
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
WORK = spec['work']
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tree.blend'))
S = json.load(open(os.path.join(WORK, 'impostor.json')))['size_m']
me = bpy.data.meshes.new('Tree_LOD3'); bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
vs = [bm.verts.new(p) for p in ((-S / 2, 0, 0), (S / 2, 0, 0), (S / 2, 0, S), (-S / 2, 0, S))]
f = bm.faces.new(vs)
for loop, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
    loop[uv].uv = t
bm.normal_update()
if f.normal.y > 0:
    f.normal_flip()
bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
obj = bpy.data.objects.new('Tree_LOD3', me); bpy.context.scene.collection.objects.link(obj)
white = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
white.data.foreach_set('color', [1.0] * 4 * len(me.vertices)); me.color_attributes.active_color = white
m = bpy.data.materials.new('Impostor'); m.use_nodes = True; nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = bpy.data.images.load(os.path.join(WORK, 'impostor_basecolor.png'))
nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(tb.outputs['Alpha'], bsdf.inputs['Alpha'])
tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(os.path.join(WORK, 'impostor_normal.png'))
tn.image.colorspace_settings.name = 'Non-Color'
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
bsdf.inputs['Roughness'].default_value = 0.9; bsdf.inputs['Metallic'].default_value = 0.0
m.use_backface_culling = False; m['openyamm_billboard'] = True
me.materials.append(m)
names = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']
for o in bpy.data.objects:
    o.select_set(o.name in names)
bpy.context.view_layer.objects.active = bpy.data.objects['Tree']
out = os.path.join(WORK, 'tree_export.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_extras=True, export_normals=True, export_vertex_color='ACTIVE', export_tangents=False, export_animations=False,
                          export_skins=False, export_morph=False, export_image_format='AUTO', export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tree_export.blend'))
print('EXPORTED', out)
