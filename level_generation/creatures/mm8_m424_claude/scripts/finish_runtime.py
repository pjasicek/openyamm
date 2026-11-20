import subprocess,json,hashlib,struct
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';S=P/'scripts';V=P/'review/viewer'
def run(*a):subprocess.run([str(x) for x in a],check=True)
run('python3',S/'shrink_shadow_lods.py',E/'mm8_m424_lods.glb',E/'mm8_m424_lods_shadowfix.glb')
run('python3',P.parent/'claude_shared/region_variants.py',E/'mm8_m424_lods_shadowfix.glb',E/'mm8_m424.glb',P/'textures/m424_ramps.json','--extra','M424','openyamm_specular=1','--extra','M424','openyamm_specular_mask=true','--extra','M424','pbr.metallicFactor=0','--extra','Dagger','openyamm_specular=1','--extra','Dagger','openyamm_specular_mask=true')
run('python3','tools/split_attachment.py',E/'mm8_m424.glb','--joint','Dagger','--body',E/'mm8_m424.glb','--attachment',E/'mm8_m424_dagger.glb')
run('python3','tools/merge_head_material.py',E/'mm8_m424.glb',E/'mm8_m424.glb')
run('python3',S/'viewer_tiers.py')
def glb(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n])
d=glb(E/'mm8_m424_lod0.glb')
clips={a['name']:max(d['accessors'][x['input']]['max'][0] for x in a['samplers']) for a in d['animations']}
native={'Standing':'s','Walking':'w','Running':'w','Hit':'n','Death':'d','Dead':'x','Fidget':'f'}
provenance={'Standing':'RelaxIdle, fitted civilian dagger carry','Walking':'RelaxWalkForward; native attacks also use this role','Running':'Mixamo Standard Run; source arm swing and calibrated dagger grip','Hit':'UnarmedGetHitF1 recoil applied to civilian stance','Death':'UnarmedDeath1 side/back fall','Dead':'Last Death pose held','Fidget':'Authored from native dagger toss: release, one turn, catch'}
m={'revision':'mm8_m424_claude_v2_arm','default_model':'m424_a','default_clip':'Standing','model':'mm8_m424_a.glb','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in zip('abc',['Green','Blue','Burgundy']):
 p=V/f'mm8_m424_{tier}.glb';h=hashlib.sha256(p.read_bytes()).hexdigest();m['models'].append({'id':f'm424_{tier}','label':f'{label} tunic ({tier.upper()})','revision':m['revision'],'url':p.name+'?v='+h[:12],'sha256':h})
m['model_sha256']=m['models'][0]['sha256']
for name,duration in clips.items():
 fs=sorted((P.parent/'mm8_m424/native_variants').glob('m424'+native[name]+'*0_425.png'))
 m['clips'][name]={'label':name,'duration':duration,'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':provenance[name],'anchors':[{'time':duration*i/max(len(fs)-1,1),'label':str(i),'source_images':['../../../mm8_m424/native_variants/'+f.name]} for i,f in enumerate(fs)]}
(V/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('MANIFEST',clips)
