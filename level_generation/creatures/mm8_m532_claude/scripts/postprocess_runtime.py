from pathlib import Path
import sys,subprocess,json,numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];repo=P.parents[2];sys.path.insert(0,str(repo/'tools'));sys.path.insert(0,str(P.parent/'claude_shared'))
from merge_head_material import read_glb,write_glb,accessor_array
import region_variants as R
src=P/'export/mm8_centaur_lods.glb';shadow=P/'export/mm8_centaur_shadow.glb';out=P/'export/mm8_centaur.glb'
d,b=read_glb(src);node=next(n for n in d['nodes']if n.get('name')=='Body');base=d['meshes'][node['mesh']]
pos=np.concatenate([accessor_array(d,b,p['attributes']['POSITION'])for p in base['primitives']]);normal=np.concatenate([accessor_array(d,b,p['attributes']['NORMAL'])for p in base['primitives']]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9);tree=cKDTree(pos);report={}
for level,mi in enumerate(base['extras']['openyamm_shadow_lods']):
    if not level:continue
    for p in d['meshes'][mi]['primitives']:
        ai=p['attributes']['POSITION'];a=d['accessors'][ai];v=d['bufferViews'][a['bufferView']];assert v.get('byteStride',12)==12
        assert sum(q['attributes']['POSITION']==ai for m in d['meshes']for q in m['primitives'])==1
        x=accessor_array(d,b,ai);_,nn=tree.query(x);n=normal[nn];dist=np.einsum('ij,ij->i',x-pos[nn],n);push=np.clip(dist+{1:.002,2:.004,3:.007}[level],0,.015);x-=n*push[:,None]
        off=v.get('byteOffset',0)+a.get('byteOffset',0);b[off:off+x.nbytes]=x.astype(np.float32).tobytes();a['min']=x.min(0).tolist();a['max']=x.max(0).tolist();report[str(level)]={'vertices':len(x),'maximum_push_metres':float(push.max())}
write_glb(shadow,d,b);R.apply_variants(shadow,out,P/'textures/centaur_ramps.json')
for joint,suffix in [('Bow','bow'),('Quiver','quiver')]:
    subprocess.run([sys.executable,str(repo/'tools/split_attachment.py'),str(out),'--joint',joint,'--body',str(out),'--attachment',str(P/'export'/f'mm8_centaur_{suffix}.glb')],check=True)
subprocess.run([sys.executable,str(repo/'tools/merge_head_material.py'),str(out),str(out)],check=True)
(P/'export/shadow_report.json').write_text(json.dumps(report,indent=2)+'\n')
