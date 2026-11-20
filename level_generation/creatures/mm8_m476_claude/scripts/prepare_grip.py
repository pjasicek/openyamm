from pathlib import Path
import runpy,sys,json
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1]
s=p/'scripts/grip_from_source.py'
sys.argv=[str(s),'--',str(Path('anim_library').resolve()/'humanoid_set/1Hand.glb'),'MaceAttackR1:0']
runpy.run_path(str(s),run_name='__main__')
f=p/'work/grip_source.json'; g=json.loads(f.read_text()); (p/'work/grip_source_right.json').write_text(json.dumps(g,indent=2))
r=json.loads((p/'work/source_rest.json').read_text()); F=Matrix.Diagonal((-1,1,1))
g['axis_hand']=list((Matrix(r['B_L_Hand']['rot']).inverted()@F@Matrix(r['B_R_Hand']['rot'])@Vector(g['axis_hand'])).normalized())
g['side']='L'; g['mirrored_from']='grip_source_right.json'; f.write_text(json.dumps(g,indent=2))
s=p/'scripts/grip_solve.py';sys.argv=[str(s),'--',str(p/'work/motion_v1.blend'),'Standing','0'];runpy.run_path(str(s),run_name='__main__')
