import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_fmp.blend'))
for mat in bpy.data.materials:
 if mat.use_nodes:
  for n in mat.node_tree.nodes:
   if n.type=='TEX_IMAGE' and 'basecolor' in n.image.name:mat.node_tree.nodes.active=n
s=bpy.context.scene;common.workbench_clay(s,True)
common.render_views(str(P/'review/feedback_v3/textured_face'),1.45,.6,views=('front',),resolution=(1000,1000))
