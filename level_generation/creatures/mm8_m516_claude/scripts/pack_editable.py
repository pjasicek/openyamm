import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m516.blend'))
for obj,slot,label in [('Body',0,'body'),('Body',1,'head')]:
 mat=bpy.data.objects[obj].data.materials[slot];bs=mat.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(P/'textures'/f'm516_{label}_native_a.png'),check_existing=True);node.image.pack()
for mat in bpy.data.objects['Body'].data.materials:
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and 'native_a' not in node.image.filepath:
   path=Path(node.image.filepath);node.image=bpy.data.images.load(str(P/'textures'/path.name),check_existing=False);node.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m516.blend'))
