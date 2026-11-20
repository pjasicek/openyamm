from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];s=p/'scripts/proportions.py'
sys.argv=[str(s),'--','source',str(p.parents[2]/'anim_library/humanoid_set/Relax.glb')];runpy.run_path(str(s),run_name='__main__')
sys.argv=[str(s),'--','target',str(p/'work/ready_final.blend'),'Rig','Body',str(p/'work/identity_bone_map.json')];runpy.run_path(str(s),run_name='__main__')
s=p/'scripts/build_lods.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
