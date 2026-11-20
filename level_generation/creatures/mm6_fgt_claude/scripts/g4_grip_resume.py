from pathlib import Path
import sys,runpy,os,json
p=Path(__file__).resolve().parents[1];lib=p.parents[2]/'anim_library/humanoid_set'
sys.path.insert(0,str(p/'scripts'))
def run(name,*args):
 sys.argv=[str(p/'scripts'/name),'--',*map(str,args)]
 runpy.run_path(sys.argv[0],run_name='__main__')
roles={'Standing':('Armed','ArmedIdle'),'Walking':('Armed','ArmedWalk'),'Running':('Armed','ArmedRunForward'),'Attack':('1Hand','SwordAttackR3'),'Hit':('Armed','ArmedGetHitF1'),'Death':('Armed','ArmedDeath1')}
run('reduce_rigged.py',p/'work/rig_v4f.blend',p/'work/rig_v4.blend')
run('grip_from_source.py',lib/'1Hand.glb','SwordAttackR3:0')
os.environ['GRIP_RENDER']=str(p/'review/grip')
run('grip_solve.py',p/'work/rig_v4.blend','Standing','8')
run('apply_grip.py',p/'work/rig_v4.blend',p/'work/rig_v5.blend')
run('g4_weights.py',p/'work/rig_v5.blend','initial','Standing:0','Walking:6','Running:6','Attack:4','Attack:7','Attack:9','Attack:12','Hit:6','Death:20')
run('g5_hand_stretch.py',p/'work/rig_v5.blend',*roles)
for view in ('front','three_quarter','left'):
 run('clip_sheet.py',p/'work/rig_v5.blend',p/f'review/clay_{view}',view,'7',*roles)
