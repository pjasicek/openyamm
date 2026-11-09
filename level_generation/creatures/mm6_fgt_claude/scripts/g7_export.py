from pathlib import Path
import sys,runpy,json,bpy
p=Path(__file__).resolve().parents[1];s=p/'scripts';lib=p.parents[2]/'anim_library/humanoid_set'
runpy.run_path(str(s/'g1_rom.py'),run_name='__main__')
# Proportions are measured from the bind pose, independent of the active animation.
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'))
r=bpy.data.objects['Rig'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_proportions.blend'))
json.dump({b.name:b.name for b in r.data.bones},open(p/'work/bone_map.json','w'))
sys.argv=[str(s/'proportions.py'),'--','target',str(p/'work/rig_proportions.blend'),'Rig','Body',str(p/'work/bone_map.json')]
runpy.run_path(sys.argv[0],run_name='__main__')
runpy.run_path(str(s/'export_review.py'),run_name='__main__')
roles={'Standing':('Armed','ArmedIdle'),'Walking':('Armed','ArmedWalk'),'Running':('Armed','ArmedRunForward'),'Attack':('1Hand','SwordAttackR3'),'Hit':('Armed','ArmedGetHitF1'),'Death':('Armed','ArmedKnockdown1')}
sys.argv=[str(s/'trace_export.py'),'--',str(p/'review/viewer/mm6_fgt_clay.glb')]+[f'{r}={lib/(st+".glb")}:{c}' for r,(st,c) in roles.items()]
runpy.run_path(sys.argv[0],run_name='__main__')
