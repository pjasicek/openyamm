from pathlib import Path
import bpy,sys,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import common
def run(name,args):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
a=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
run('g6_contacts.py',[p/'work/rig_v5t.blend',*a])
run('g4_weights.py',[p/'work/rig_v5t.blend','final','Walking:6','Running:6','Attack:16','Attack:20','Attack:24','Attack:28','Hit:6','Fidget:11','Death:14','Death:28'])
run('g5_hand_stretch.py',[p/'work/rig_v5t.blend',*a])
run('trace_export.py',[p/'review/viewer/mm6_ogr_clay.glb','Walking=anim_library/humanoid_set/Armed.glb:ArmedWalk','Running=anim_library/humanoid_set/Armed.glb:ArmedRunForward','Attack=anim_library/humanoid_set/1Hand.glb:SwordAttackR6','Hit=anim_library/humanoid_set/Armed.glb:ArmedGetHitF1'])
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5t.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];print('REAR_SKIN_REST631',tuple(body.data.vertices[631].co))
a=bpy.data.actions['Walking'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(4)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/rear_cloth_walk4'),.9,.7,views=('back','left'),resolution=(700,700))
for view in ('front','left','three_quarter'):
 run('clip_sheet.py',[p/'work/rig_v5t.blend',p/'review'/('final_clay_'+view),view,7,'Standing','Attack','Fidget','Death'])
