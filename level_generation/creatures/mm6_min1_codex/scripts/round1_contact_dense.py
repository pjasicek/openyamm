import bpy,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_clothed.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard'
for f in [45,55,70,100]:
 r.animation_data.action=bpy.data.actions['Attack'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(f);common.render_views(str(P/f'review/round1/contact_before_{f}'),1,2.8,views=['front','left','three_quarter'],resolution=(640,640))
runpy.run_path(str(P/'scripts/round1_contacts.py'),run_name='__main__',init_globals={'INPUT':'work/round1_clothed.blend','OUTPUT':'work/round1_contact_dense.blend','REPORT':'review/round1/contact_dense.json','ROLES':['Attack','Cast']})
runpy.run_path(str(P/'scripts/round1_cloth.py'),run_name='__main__',init_globals={'INPUT':'work/round1_contact_dense.blend'})
sys.argv=['rig_gates_48.py','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
