"""Use the shared single-atlas merger once per LOD, since each LOD has its own map resolution."""
import sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];root=P.parents[2];sys.path.insert(0,str(root/'tools'))
from merge_head_material import read_glb,write_glb
path=P/'export/mm6_figc.glb'
for level in range(4):
 d,b=read_glb(path)
 for mat in d['materials']:
  name=mat['name']
  if 'Head' not in name and 'Cranium' not in name:continue
  actual=next((i for i in range(1,4) if f'_LOD{i}_' in name),0)
  mat['name']=name.replace('Head','Cranium') if actual!=level else name.replace('Cranium','Head')
 write_glb(path,d,b)
 subprocess.run([sys.executable,str(root/'tools/merge_head_material.py'),str(path),str(path)],check=True)
d,b=read_glb(path);base=d['meshes'][0]
assert all(len(d['meshes'][i]['primitives'])==1 for i in [0]+base['extras']['openyamm_lods'])
assert not any('Cranium' in m['name'] for m in d['materials'])
