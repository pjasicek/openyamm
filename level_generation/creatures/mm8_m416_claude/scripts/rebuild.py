"""Rebuild the selected textured revision; original Meshy outputs and UV transfer stay frozen."""
from pathlib import Path
import argparse,subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
a=argparse.ArgumentParser();a.add_argument('--token',required=True);args=a.parse_args()
def ordinary(script,*extra):
 subprocess.run([sys.executable,str(repo/'tools/creature_workspace.py'),'run','--project',str(p),'--token',args.token,'--',sys.executable,str(script),*map(str,extra)],cwd=repo,check=True)
def blender(script):
 subprocess.run([str(repo/'tools/run_creature_blender.sh'),'--token',args.token,str(p/'scripts'/script)],cwd=repo,check=True)
blender('fit_hanging_quiver.py')
ordinary(repo/'tools/prepare_actor_glb.py',p/'export/mm8_m416_lod0.glb',p/'export/mm8_m416_runtime_lod0.glb')
blender('build_lods.py')
for n in ['postprocess_runtime.py','verify_runtime.py','viewer_tiers.py']:ordinary(p/'scripts'/n)
blender('audit_final_author.py')
print('Rebuilt and numerically checked. Review playback and native captures before reinstalling.')
