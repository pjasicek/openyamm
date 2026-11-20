import runpy,bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];runpy.run_path(str(P/'scripts/round2_shirt_weights.py'),run_name='__main__');sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/body_lod0.blend'));C.reset();r=bpy.data.objects['Rig'];s=bpy.context.scene;common.workbench_clay(s);s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.2,.5,.3)
for role,t in [('Standing',0),('Attack',.4),('Death',1.3)]:
 C.activate(role,t);common.render_views(str(P/'review/round2'/f'clay_anatomical_{role}'),1.23,1.2,views=('front','left','back'),resolution=(700,800))
