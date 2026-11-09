from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for s in ['g6_sword_mesh.py','trace_export.py']:
 sys.argv=[s,'--',str(p/'export/mm6_ogr_runtime_lod0.glb')]
 if s=='trace_export.py':
  lib=p.parents[2]/'anim_library/humanoid_set'
  sys.argv += [f'{role}={lib/file}:{clip}' for role,file,clip in [('Standing','Relax.glb','RelaxIdle'),('Walking','Armed.glb','ArmedWalk'),('Running','Relax.glb','RelaxRunForward'),('Fidget','Armed.glb','ArmedIdleAlert1'),('Death','Unarmed.glb','UnarmedDeath1'),('Hit','Armed.glb','ArmedGetHitF1'),('Attack','1Hand.glb','SwordAttackR6')]]
 runpy.run_path(str(p/'scripts'/s),run_name='__main__')
