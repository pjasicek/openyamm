import bpy,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_min1_axe.glb'));sc=bpy.context.scene
for mat in bpy.data.materials:
 bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
points=np.array([tuple(o.matrix_world@v.co) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices]);lo=points.min(0);hi=points.max(0);c=(lo+hi)/2;common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard';sc.display.shading.show_specular_highlight=False
common.render_views(str(P/'review/axe'),float(c[2]),float(np.max(hi-lo)*1.15),views=['front','three_quarter'],resolution=(768,768),target=tuple(c[:2]))
