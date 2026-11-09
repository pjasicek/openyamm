from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
def run(name,args):
 s=p/"scripts"/name;sys.argv=[str(s),"--"]+list(map(str,args));runpy.run_path(str(s),run_name="__main__")
run("check_motion.py",["rig_uv","hit_repaired","Hit"])
run("stride.py",[p/"work/rig_uv.blend","Walking"])
run("jerk_probe.py",[p/"work/motion_sources.blend","Walking","Attack","Hit","Death"])
