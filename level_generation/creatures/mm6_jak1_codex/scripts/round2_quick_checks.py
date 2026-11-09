import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('batch_pose_audit.py');run('grip_floor_audit.py')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));bpy.data.objects['Jackalman'].name='Body';bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_gate_master.blend'))
roles=['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
run('g4_weights.py',[P/'work/final_gate_master.blend','final',*[f'{n}:{f}'for n in roles for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,max(1,bpy.context.scene.render.fps//48))]])
run('g5_hand_stretch.py',[P/'work/final_gate_master.blend',*roles])
