from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m620.blend'))
common.setup_render();common.workbench_clay(bpy.context.scene,True)
for m in bpy.data.objects['Bedraggled'].data.materials:
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and 'basecolor' in n.image.name:m.node_tree.nodes.active=n
common.render_views(str(p/'review/head_actual'),1.51,.44,views=('front','left','back','right','three_quarter'),resolution=(768,768))
