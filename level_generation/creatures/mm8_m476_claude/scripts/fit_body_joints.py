from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
steps=[('meshy_joints.py',[str(p/'meshy/rig_v1/result_rigged_character_glb_url.glb'),str(p/'work/step1.blend')]),('fit_joints.py',[str(p/'work/step1.blend'),'Body']),('compose_joints.py',[]),('joint_xray.py',[str(p/'work/step1.blend'),'Body',str(p/'work/joints_final.json'),str(p/'review/joints'),str(p/'work/meshy_joints.json')])]
for name,args in steps:
    script=p/'scripts'/name;sys.argv=[str(script),'--',*args];runpy.run_path(str(script),run_name='__main__')
