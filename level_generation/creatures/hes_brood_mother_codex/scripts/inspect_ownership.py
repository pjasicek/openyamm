import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/texture_ready.blend'))
o=bpy.data.objects['BroodMother'];me=o.data;names={g.index:g.name for g in o.vertex_groups}
colors=me.color_attributes.new(name='Owners',type='FLOAT_COLOR',domain='POINT')
for v in me.vertices:
 w={names[g.group]:g.weight for g in v.groups};head=w.get('B_Head',0);base=w.get('Base',0)
 colors.data[v.index].color=(base,head,1-base-head,1)
mat=bpy.data.materials.new('Ownership');mat.use_nodes=True
node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='Owners'
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
me.materials.clear();me.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/ownership.blend'))
