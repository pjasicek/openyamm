"""Cycles ambient occlusion on the locked layout (README.md): work/<template>/maps/ao.png, 2048, for the grade and the
MR map's occlusion channel. Usage: blender --background --python bake_ao.py -- <template>"""
import bpy, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
NAME = sys.argv[sys.argv.index('--') + 1]
WORK = os.path.join(PROJECT, 'work', NAME)
os.makedirs(os.path.join(WORK, 'maps'), exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'layout.blend'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
# For the bake, faces point out, with plain smooth normals. Layouts made before fix_winding.py have the templates' old
# winding (against their normals): those are reversed.
import bmesh
me = obj.data
against = sum(sum(p.normal.dot(me.loops[l].normal) for l in p.loop_indices) < 0 for p in me.polygons)
print('BAKE faces against their normals', against, 'of', len(me.polygons))
if against > len(me.polygons) / 2:
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
if obj.data.has_custom_normals:
    obj.data.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(obj.data.loops))
for p in obj.data.polygons:
    p.use_smooth = True
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.render.bake.margin = 8
scene.world = scene.world or bpy.data.worlds.new('w')
# Occlusion within a few centimetres: the fuller, the guard's junctions, the grip bands (Oblivion units ~1.43 cm).
scene.world.light_settings.distance = 4.0
img = bpy.data.images.new('ao', 2048, 2048, alpha=False)
img.colorspace_settings.name = 'Non-Color'
mat = bpy.data.materials.new('ao'); mat.use_nodes = True
nt = mat.node_tree
node = nt.nodes.new('ShaderNodeTexImage'); node.image = img
nt.nodes.active = node
# The AO shader node baked as emission (the AO bake pass came out black on these meshes).
aon = nt.nodes.new('ShaderNodeAmbientOcclusion'); aon.inputs['Distance'].default_value = 4.0; aon.samples = 64
emit = nt.nodes.new('ShaderNodeEmission')
nt.links.new(aon.outputs['AO'], emit.inputs['Color'])
nt.links.new(emit.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
obj.data.materials.clear(); obj.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.bake(type='EMIT')
img.filepath_raw = os.path.join(WORK, 'maps', 'ao.png'); img.file_format = 'PNG'; img.save()
print('BAKE ao done', NAME)
