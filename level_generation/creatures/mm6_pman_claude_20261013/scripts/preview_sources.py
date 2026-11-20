"""G1: inspect civilian choices on their own source mannequin before modelling."""
from pathlib import Path
import bpy,sys,runpy,json,math
from mathutils import Vector
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
sys.path.insert(0,str(p/'scripts'));import common
rows=[]
for name in ('Standard Idle','Standard Walk','Neck Stretching'):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(repo/'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'))
 arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');meshes=[o for o in bpy.data.objects if o.type=='MESH']
 before=set(bpy.data.objects);acts=set(bpy.data.actions)
 bpy.ops.import_scene.fbx(filepath=str(repo/'anim_library/mixamo'/('_discarded' if name=='Neck Stretching' else '')/(name+'.fbx')))
 source=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE');act=source.animation_data.action
 # Both files use the library character's identical named rig.
 assert set(b.name for b in source.data.bones).issubset(set(b.name for b in arm.data.bones))
 arm.animation_data_create();arm.animation_data.action=act;arm.animation_data.action_slot=act.slots[0]
 for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
 lo,hi=common.world_bounds(meshes);h=hi.z-lo.z
 scene=bpy.context.scene;common.workbench_clay(scene)
 f0,f1=act.frame_range;row=[]
 for i in range(4):
  f=f0+(f1-f0)*i/3;scene.frame_set(int(f),subframe=f%1)
  for view in ('front','left','three_quarter'):
   prefix=p/'review/g1_mixamo'/f'{name.replace(" ","_")}_{i}';prefix.parent.mkdir(exist_ok=True)
   files=common.render_views(str(prefix),(lo.z+hi.z)/2,h*1.2,views=(view,),resolution=(240,380),target=((lo.x+hi.x)/2,(lo.y+hi.y)/2))
   row.append([files[0],f'{name} {f:.1f} {view}'])
 rows.append(row)
(p/'review/g1_mixamo/frames.json').write_text(json.dumps(rows)+'\n')
for view in ('front','left','three_quarter'):
 sys.argv=['rpg_preview.py','--',str(repo/'anim_library/humanoid_set/Unarmed.glb'),str(p/'review'/('g1_unarmed_'+view)),view,'4','UnarmedGetHitF1','UnarmedDeath1']
 runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['rom_extract.py','--',f'Hit={repo}/anim_library/humanoid_set/Unarmed.glb:UnarmedGetHitF1',f'Death={repo}/anim_library/humanoid_set/Unarmed.glb:UnarmedDeath1']
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
