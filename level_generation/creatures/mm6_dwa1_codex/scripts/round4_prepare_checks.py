import sys,json,copy,hashlib,numpy as np
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'scripts'),str(P.parents[2]/'tools')]
from merge_head_material import read_glb,write_glb,accessor_array,compact
from normalize_lod_weights import normalize_weights
b=P/'work/round4_before';old,ob=read_glb(b/'export/mm6_dwa1.glb');new,nb=read_glb(P/'export/mm6_dwa1.glb');h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest();proof={}
for x in old['animations']:
 y=next(a for a in new['animations']if a['name']==x['name']);assert x['channels']==y['channels']
 for a,z in zip(x['samplers'],y['samplers']):
  for k in ['input','output']:assert np.array_equal(accessor_array(old,ob,a[k]),accessor_array(new,nb,z[k]))
 proof[x['name']]='byte-identical animation samples/channels'
assert old['nodes']==new['nodes']
for a,z in zip(old['skins'],new['skins']):
 assert a['joints']==z['joints'];assert np.array_equal(accessor_array(old,ob,a['inverseBindMatrices']),accessor_array(new,nb,z['inverseBindMatrices']))
def images(d,b):
 result=[]
 for i in d['images']:
  v=d['bufferViews'][i['bufferView']];o=v.get('byteOffset',0);result.append(hashlib.sha256(bytes(b[o:o+v['byteLength']])).hexdigest())
 return sorted(result)
assert images(old,ob)==images(new,nb)
assert (P/'integration/actors.yml').read_bytes()==(b/'integration/actors.yml').read_bytes()
assert old['materials']==new['materials']
(P/'review/round4/artifact_parity.json').write_text(json.dumps({'runtime_sha256':h,'protected_clips':proof,'materials_textures_rest_rig':'exact','actors_yml_sha256':hashlib.sha256((P/'integration/actors.yml').read_bytes()).hexdigest(),'actors_yml_changed':False,'pass':True},indent=2)+'\n')

# Use the actual regenerated LOD geometry/weights for every close-up, with tier A baked for Three/Blender.
d,bin=read_glb(P/'export/mm6_dwa1_lods.glb');normalize_weights(d,bin)
node=next(n for n in d['nodes']if n.get('name')=='Dwarf');levels=[node['mesh'],*d['meshes'][node['mesh']]['extras']['openyamm_lods']]
for i,mi in enumerate(levels):
 copydoc=copy.deepcopy(d);next(n for n in copydoc['nodes']if n.get('name')=='Dwarf')['mesh']=mi;write_glb(P/f'work/round4/final_unbaked_lod{i}.glb',*compact(copydoc,bin))

for mat in d['materials']:
 name=mat['name'].split('.')[0]
 if name not in ['Dwarf_A','DwarfHead_A']:continue
 payload=(P/f'work/tier_dwa1_a_{name}.png').read_bytes();bin.extend(bytes(-len(bin)%4));bv=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(bin),'byteLength':len(payload)});bin.extend(payload);im=len(d['images']);d['images'].append({'bufferView':bv,'mimeType':'image/png'});tx=len(d['textures']);d['textures'].append({'source':im});mat['pbrMetallicRoughness']['baseColorTexture']['index']=tx
node=next(n for n in d['nodes']if n.get('name')=='Dwarf');levels=[node['mesh'],*d['meshes'][node['mesh']]['extras']['openyamm_lods']]
for i,mi in enumerate(levels):
 copydoc=copy.deepcopy(d);next(n for n in copydoc['nodes']if n.get('name')=='Dwarf')['mesh']=mi;write_glb(P/f'work/lod_review_{i}.glb',*compact(copydoc,bin))
f=P/'review/viewer/manifest.json';m=json.loads(f.read_text());m.update(revision='mm6_dwa1_codex_review4',runtime_artifact_sha256=h)
for row in m['models']:
 path=P/'review/viewer'/f"mm6_{row['id']}.glb";sha=hashlib.sha256(path.read_bytes()).hexdigest();row.update(sha256=sha,url=path.name+'?v='+sha[:12],revision='mm6_dwa1_codex_review4')
f.write_text(json.dumps(m,indent=2)+'\n')
