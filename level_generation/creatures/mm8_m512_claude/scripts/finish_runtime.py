"""Preserve LOD0/rig/clips, add three colour and shadow LODs, then shared palette variants."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

PROJECT=Path(__file__).resolve().parents[1];REPO=PROJECT.parents[2];OUT=PROJECT/'export'
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import read_glb,write_glb,generate
sys.path.insert(0,str(PROJECT.parent/'mm6_rat_claude/scripts'))
from shrink_shadow_lods import view
doc,binary=read_glb(OUT/'wolf_lods.glb');binary=bytearray(binary)
node=next(n for n in doc['nodes'] if n.get('name')=='Wolf');base=doc['meshes'][node['mesh']]
primitive=base['primitives'][0];assert len(base['primitives'])==1
positions=view(doc,binary,primitive['attributes']['POSITION'])[0].astype(float)
normals=view(doc,binary,primitive['attributes']['NORMAL'])[0].astype(float)
normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-9)
tree=cKDTree(positions);height=float(np.ptp(positions[:,1]));report={}
for level,index in enumerate(base['extras']['openyamm_shadow_lods'][1:],1):
    for primitive in doc['meshes'][index]['primitives']:
        accessor=primitive['attributes']['POSITION'];value,offset=view(doc,binary,accessor);value=value.astype(float)
        assert sum(p['attributes']['POSITION']==accessor for m in doc['meshes'] for p in m['primitives'])==1
        _,nearest=tree.query(value);n=normals[nearest]
        distance=np.einsum('ij,ij->i',value-positions[nearest],n)
        margin=[.004,.007,.012][level-1]*height/1.57
        push=np.clip(distance+margin,0,.015*height/1.57);value-=n*push[:,None]
        binary[offset:offset+value.size*4]=value.astype('<f4').tobytes()
        doc['accessors'][accessor].update(min=value.min(0).tolist(),max=value.max(0).tolist())
        report[str(level)]={'margin_m':margin,'maximum_push_m':float(push.max())}
# Translate Blender's zero-specular extension to the engine's equivalent material extra.
for material in doc['materials']:
    extension=material.get('extensions',{}).pop('KHR_materials_specular',None)
    assert extension is None or extension=={'specularFactor':0}
    material.setdefault('extras',{})['openyamm_specular']=0
    if not material.get('extensions'):material.pop('extensions',None)
for key in ['extensionsUsed','extensionsRequired']:
    if key in doc:
        doc[key]=[name for name in doc[key] if name!='KHR_materials_specular']
        if not doc[key]:doc.pop(key)
write_glb(OUT/'wolf_shadow.glb',doc,binary)
(PROJECT/'work/shadow_report.json').write_text(json.dumps(report,indent=2)+'\n')
subprocess.run(['/usr/bin/python3',str(PROJECT.parent/'claude_shared/region_variants.py'),
                str(OUT/'wolf_shadow.glb'),str(OUT/'mm8_wolf.glb'),str(PROJECT/'textures/wolf_ramps.json'),
                '--extra','Wolf','openyamm_specular=0','--extra','Wolf','pbr.metallicFactor=0'],check=True)
print('RUNTIME',OUT/'mm8_wolf.glb',flush=True)
