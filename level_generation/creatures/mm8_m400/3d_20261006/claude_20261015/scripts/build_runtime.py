import sys, subprocess, json, struct, io
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];REPO=P.parents[4];D=P/'delivery'
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import read_glb, write_glb, generate, accessor_bytes
doc,binary=read_glb(D/'export_raw.glb');binary=bytearray(binary)
walk=next(a for a in doc['animations'] if a['name']=='Walk')
for index in {s['input'] for s in walk['samplers']}:
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    times=np.frombuffer(binary,dtype='<f4',count=a['count'],offset=offset)
    times*=np.float32((31/30)/(50/48));a['min']=[float(times.min())];a['max']=[float(times.max())]
del times
assert abs(max(doc['accessors'][s['input']]['max'][0] for s in walk['samplers'])-31/30)<1e-5
for m,label in zip(doc['materials'],['Body','Head']):
    # Blender repacks G/B; preserve the authored per-texel specular in the unused red channel.
    ti=m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];ii=doc['textures'][ti]['source']
    data=(P/'textures'/f'{label}_mr.png').read_bytes();binary.extend(b'\0'*(-len(binary)%4))
    vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)})
    binary.extend(data);doc['images'][ii]={'name':label+'_mr','bufferView':vi,'mimeType':'image/png'}
    m['pbrMetallicRoughness']['metallicFactor']=0
write_glb(D/'export_prepared_input.glb',doc,binary)
subprocess.run(['/usr/bin/python3',str(REPO/'tools/prepare_actor_glb.py'),str(D/'export_prepared_input.glb'),str(D/'mm8_lizardman_peasant_lod0.glb')],check=True)
generate(D/'mm8_lizardman_peasant_lod0.glb',D/'lods.glb','Lizardman_Body',ratios=(.5,.25,.125))
commands=[
 [str(P/'scripts/shrink_shadow_lods.py'),str(D/'lods.glb'),str(D/'shadow.glb')],
 [str(REPO/'level_generation/creatures/claude_shared/region_variants.py'),str(D/'shadow.glb'),str(D/'variants.glb'),str(P/'textures/ramps.json')],
 [str(REPO/'tools/merge_head_material.py'),str(D/'variants.glb'),str(D/'mm8_lizardman_peasant.glb')]]
for cmd in commands:subprocess.run(['/usr/bin/python3',*cmd],check=True)
doc,_=read_glb(D/'mm8_lizardman_peasant.glb');base=doc['meshes'][doc['nodes'][next(i for i,n in enumerate(doc['nodes']) if n.get('name')=='Lizardman_Body')]['mesh']]
print('FINAL LOD TRIANGLES',[sum(doc['accessors'][p['indices']]['count']//3 for p in m['primitives']) for m in [base]+[doc['meshes'][i] for i in base['extras']['openyamm_lods']]],flush=True)
