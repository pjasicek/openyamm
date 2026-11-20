import sys,runpy,json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));import merge_head_material as G
runpy.run_path(str(P/'scripts/round2_package_runtime.py'),run_name='__main__')
# Identical shared atlas images must have a single texture resource across the four LODs.
d,b=G.read_glb(P/'export/mm6_mer1.glb');cache={};remap={}
for i,t in enumerate(d['textures']):
 im,_=G.image_of(d,b,i);key=(im.size,im.mode,hashlib.sha256(im.tobytes()).hexdigest(),json.dumps(d.get('samplers',[])[t['sampler']]if 'sampler'in t else{},sort_keys=True));remap[i]=cache.setdefault(key,i)
def refs(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if (k.endswith('Texture')or k=='openyamm_region_mask')and isinstance(v,dict)and 'index'in v:v['index']=remap[v['index']]
   else:refs(v)
 elif isinstance(x,list):
  for v in x:refs(v)
refs(d['materials']);d,b=G.compact(d,b);G.write_glb(P/'export/mm6_mer1.glb',d,b)
shutil.copyfile(P/'work/round2/club_accepted.glb',P/'export/mm6_mer1_club.glb')
(P/'review/round2/shared_atlas.json').write_text(json.dumps({'images':len(d['images']),'textures':len(d['textures']),'image_sizes':[list(G.image_of(d,b,i)[0].size)for i in range(len(d['textures']))],'club_byte_identical':True},indent=2))
