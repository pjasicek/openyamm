from pathlib import Path
import runpy,sys,json
p=Path(__file__).resolve().parents[1]
steps=[('fit_joints.py',[str(p/'work/step1.blend'),'Body']),('compose_joints.py',[]),('build_rig.py',[]),('fit_fingers.py',[str(p/'work/rig_v1.blend')]),('finger_joints.py',[str(p/'work/rig_v1.blend')]),('build_rig.py',[]),('hand_frame_check.py',[str(p/'work/rig_v1.blend')]),('hand_xray.py',[str(p/'work/rig_v1.blend'),'R',str(p/'review/hand_R')]),('hand_xray.py',[str(p/'work/rig_v1.blend'),'L',str(p/'review/hand_L')])]
for name,args in steps:
    script=p/'scripts'/name;sys.argv=[str(script),'--',*args];runpy.run_path(str(script),run_name='__main__')
    if name=='fit_fingers.py':
        fit=json.loads((p/'work/fingers_fit.json').read_text())
        assert set(fit)=={'L','R'} and all(all(n in fit[s] for n in ['thumb','index','middle','ring','pinky']) for s in fit)
