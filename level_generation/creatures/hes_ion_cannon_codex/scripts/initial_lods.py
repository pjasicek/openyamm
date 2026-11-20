"""Seed static chains, then use the shared repair tools for initial collapse and a texture-safe LOD1."""
import copy
import os
from pathlib import Path
import subprocess
import sys
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(R/'tools'))
from build_actor_lods import read_glb,write_glb,merge_shadow
H=R/'level_generation/creatures/lod_repair_claude/scripts'
PYTHON=os.environ['LOD_REPAIR_PYTHON']
d,b=read_glb(P/'work/ion_cannon_lod0.glb');b=bytearray(b)
base=d['meshes'][0]
for level in (1,2,3):
    mesh=copy.deepcopy(base);mesh['name']=f'IonCannon_LOD{level}';d['meshes'].append(mesh)
shadows=[]
for index in range(4):
    shadows.append(len(d['meshes']));d['meshes'].append(merge_shadow(d,b,d['meshes'][index]))
base['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':shadows}
seed=P/'work/ion_cannon_lod_seed.glb';write_glb(seed,d,b)
built=P/'work/ion_cannon_lods_built.glb';bake=P/'work/lod1_bake'
commands=[['build_lods.py',seed,'IonCannon',built,'1:0.5,2:0.25,3:0.125'],
          ['unwrap_lods.py',built,'IonCannon',bake,'1:1024'],
          ['transfer_textures.py',built,'IonCannon',bake,'1'],
          ['apply_bake.py',built,'IonCannon',bake,P/'work/ion_cannon_initial_lods.glb','1']]
for script,*args in commands:
    subprocess.run([PYTHON,'-B',str(H/script),*map(str,args)],check=True)
print('Initial static LODs ready; LOD1 has its own reprojected atlas.')
