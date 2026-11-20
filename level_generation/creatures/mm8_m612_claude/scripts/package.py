import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(P.parent/'claude_shared')]
import region_variants as rv
import material_classes_to_orm as orm
from merge_head_material import accessor_array
def run(*args):subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,check=True)
e=P/'export';t=P/'textures'
rv.apply_variants(e/'gog_lods.glb',e/'gog_variants.glb',t/'gog_ramps.json',
    [('Gog','openyamm_specular',1.0),('Gog','openyamm_specular_mask',True)])
report=orm.convert(e/'gog_variants.glb',e/'gog_materials.glb',[
    ('GogHead',None,t/'gog_head_material_classes.png'),('Gog',t/'gog_material_classes.png',None)])
(P/'work/material_report.json').write_text(json.dumps(report,indent=2)+'\n')
run(ROOT/'tools/merge_head_material.py',e/'gog_materials.glb',e/'mm8_m612.glb')
d,b=rv.read_glb(e/'mm8_m612.glb');nodes={n.get('name'):i for i,n in enumerate(d['nodes'])}
assert all(x in nodes for x in ['Body','Socket_LeftPalm','Socket_RightPalm','Socket_LeftEye','Socket_RightEye'])
assert not any('wing' in n.lower() for n in nodes)
assert len(d['skins'][0]['joints'])==60
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['gog_a','gog_b','gog_c']
assert len(d['images'])==4 and len(d['materials'])==3
mesh=d['meshes'][d['nodes'][nodes['Body']]['mesh']]
assert len(mesh['extras']['openyamm_lods'])==3 and len(mesh['extras']['openyamm_shadow_lods'])==4
for m in d['meshes']:
    assert len(m['primitives'])==1
    attrs=m['primitives'][0]['attributes']
    assert 'JOINTS_1' in attrs and 'WEIGHTS_1' in attrs
    import numpy as np
    w=accessor_array(d,b,attrs['WEIGHTS_0'])+accessor_array(d,b,attrs['WEIGHTS_1'])
    assert np.max(abs(w.sum(1)-1))<1e-5
durations={a['name']:max(float(accessor_array(d,b,s['input']).max()) for s in a['samplers']) for a in d['animations']}
assert len(durations)==9
assert abs(durations['Attack']-53/30)<1e-5 and abs(durations['Cast']-53/30)<1e-5
manifest=P/'review/viewer/manifest.json';m=json.loads(manifest.read_text());m.update(revision='gog_textured_60hz_v2',default_model='gog_a',model='gog_a.glb')
m['clips']['Hit']['duration']=.75
m['models']=[]
for tier,label in zip('abc',('Smoke Gog','Ember Gog','Fire Gog')):
    path=P/f'review/viewer/gog_{tier}.glb';h=hashlib.sha256(path.read_bytes()).hexdigest()
    m['models'].append({'id':f'gog_{tier}','label':label,'revision':m['revision'],'url':f'gog_{tier}.glb?v={h[:12]}','sha256':h})
manifest.write_text(json.dumps(m,indent=2)+'\n')
(P/'work/package_check.json').write_text(json.dumps({'clips':durations,'bones':60,'wing_bones':0,
    'materials':3,'embedded_images':4,'influences':8,'sha256':hashlib.sha256((e/'mm8_m612.glb').read_bytes()).hexdigest()},indent=2)+'\n')
print('PACKAGE',durations)
