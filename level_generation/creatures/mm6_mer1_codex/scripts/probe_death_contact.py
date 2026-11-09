import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
for name in ['before_death_surface','reduction_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{name}.blend'));C.activate('Death',1.25);print('LEG',name,[(n,tuple(bpy.data.objects['Rig'].pose.bones['B_L_'+n].head))for n in ['Thigh','Calf','Foot']],flush=True);common.workbench_clay(bpy.context.scene,True);lo,hi=common.world_bounds([bpy.data.objects['Body']]);mid=(lo+hi)*.5;common.render_views(str(P/f'review/{name}_contact'),mid.z,2.1,views=('front','left','three_quarter'),resolution=(800,800),target=(mid.x,mid.y))
