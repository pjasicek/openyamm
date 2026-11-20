from pathlib import Path
import runpy,sys,bpy
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/fit_head.py'),run_name='__main__')
s=p/'scripts/reduce_rigged.py';sys.argv=[str(s),'--',str(p/'work/head_fitted.blend'),str(p/'work/reduced.blend')];runpy.run_path(str(s),run_name='__main__')
sys.path.insert(0,str(p/'scripts'));import common
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/reduced'),1.0,2.05,views=('front','left','back'),resolution=(420,620))
common.render_views(str(p/'review/reduced_head'),1.68,0.43,views=('front','left'),resolution=(500,500))
