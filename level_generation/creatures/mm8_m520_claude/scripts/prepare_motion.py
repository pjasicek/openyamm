from pathlib import Path
import bpy,sys,runpy,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
s=p/'scripts/foot_level.py';sys.argv=[str(s),'--',str(p/'work/rig_surface.blend'),str(p/'work/rig_feet.blend'),'Standing','Walking:const','Running:const','Hit','Fidget','Death:until=30'];runpy.run_path(str(s),run_name='__main__')
s=p/'scripts/retarget_mixamo.py';sys.argv=[str(s),'--',str(p/'work/rig_feet.blend'),str(p/'work/motion_sources.blend'),'anim_library/mixamo/_discarded/Throw In.fbx:AttackSource:plant'];runpy.run_path(str(s),run_name='__main__')
rig=bpy.data.objects['Rig'];a=bpy.data.actions['AttackSource'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
common.workbench_clay(bpy.context.scene);rows=[]
for f in range(0,84,5):
 bpy.context.scene.frame_set(f)
 row={'frame':f,'hands':{s:list(rig.pose.bones[f'B_{s}_Hand'].head) for s in 'LR'}};rows.append(row)
 common.render_views(str(p/f'review/attack_source_{f:02}'),1.4,3,views=('front','left'),resolution=(400,600))
(p/'work/attack_source.json').write_text(json.dumps(rows,indent=2))
