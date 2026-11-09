import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name,args in [('meshy_joints',[str(p/'meshy/rig_v1/result_rigged_character_glb_url.glb'),str(p/'work/step1.blend')]),('compose_joints',[]),('joint_xray',[str(p/'work/step1.blend'),'Body',str(p/'work/joints_final.json'),str(p/'review/g3_joints'),str(p/'work/meshy_joints.json')]),('build_rig',[])]:
 sys.argv=[name+'.py','--',*args];runpy.run_path(str(p/'scripts'/(name+'.py')),run_name='__main__')
