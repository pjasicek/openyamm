"""Rebuild the selected textured/rigged revision; acquire a creature lease first."""
from pathlib import Path
import argparse, subprocess, sys
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--token',required=True)
a=parser.parse_args();p=Path(__file__).resolve().parents[1];repo=p.parents[2]
assert (p/'work/ready_lined.blend').is_file() and (p/'work/texture_master.blend').is_file()
def run(*args):subprocess.run([str(x) for x in args],cwd=repo,check=True)
def blender(name):run(repo/'tools/run_creature_blender.sh','--token',a.token,p/'scripts'/name)
def python(script,*args):run(sys.executable,repo/'tools/creature_workspace.py','run','--project',p,'--token',a.token,'--',sys.executable,script,*args)
blender('refresh_motion.py')
python(repo/'tools/prepare_actor_glb.py',p/'export/mm8_m604_lod0.glb',p/'export/mm8_m604_runtime_lod0.glb')
blender('build_lods.py')
python(p/'scripts/postprocess_runtime.py')
python(p/'scripts/verify_runtime.py')
python(p/'scripts/viewer_tiers.py')
blender('author_checks.py')
blender('export_parity.py')
