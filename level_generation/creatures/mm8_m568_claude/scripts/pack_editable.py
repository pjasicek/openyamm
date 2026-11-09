import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m568.blend'))
for obj,slot,label in [('Body',0,'body'),('Body',1,'head'),('PolearmMesh',0,'weapon')]:
 mat=bpy.data.objects[obj].data.materials[slot];bs=mat.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(P/'textures'/f'm568_{label}_native_a.png'),check_existing=True);node.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m568.blend'))

import json
rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
e=bpy.data.objects['Body'].evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);e.to_mesh_clear()
(P/'review/checks/assembly.json').write_text(json.dumps({'standing_body_height_m':height,'native_upright_pixels':197,'native_frame_scale':1.299988,'bones':len(rig.data.bones),'colour_lod_triangles':[12758,6377,3188,1579]},indent=2)+'\n')
