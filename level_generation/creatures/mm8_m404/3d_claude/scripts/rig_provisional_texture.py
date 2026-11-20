import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
o=bpy.data.objects['Body'];o.data.materials.clear()
mat=bpy.data.materials.new('Provisional front projection');mat.use_nodes=True
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'references_hd/01_front.png'));tex.image.pack()
bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.85
uv=o.data.uv_layers.active or o.data.uv_layers.new()
for loop in o.data.loops:
    x,y,z=o.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(.5+(x+.011)*790/1024,1-(20+(1.9-z)/1.9*1516)/1536)
o.data.materials.append(mat)
for f in o.data.polygons:f.material_index=0
for x in bpy.data.objects:x.select_set(x==o)
bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.gltf(filepath=str(p/'export/body_for_rig_textured.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
