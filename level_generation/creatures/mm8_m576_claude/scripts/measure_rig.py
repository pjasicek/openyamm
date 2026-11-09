"""Measure source frames and independent skin-ring landmarks before accepting Meshy joints."""
from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];root=p.parents[2]
for name,args in [('source_rest.py',[root/'anim_library/humanoid_set/1Hand.glb']),('fit_joints.py',[p/'work/step1.blend','Body'])]:
    sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
assert (p/'work/source_rest.json').is_file() and (p/'work/joints.json').is_file()
