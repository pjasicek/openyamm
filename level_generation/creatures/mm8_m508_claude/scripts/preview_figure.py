import bpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/figure.blend'))
body=bpy.data.objects['AirElemental_Body'];rig=bpy.data.objects['AirElemental_Rig']
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/figure'),1.70,1.2,views=('front','left','back','three_quarter'),resolution=(600,700))
(p/'work/figure_joints.json').write_text(json.dumps({b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones},indent=2))
