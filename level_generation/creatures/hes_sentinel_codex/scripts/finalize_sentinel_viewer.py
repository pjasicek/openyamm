from pathlib import Path
import hashlib,json,shutil,csv
from PIL import Image,ImageDraw
P=Path('level_generation/creatures/hes_sentinel_codex');v=P/'review/viewer'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((v/'manifest.json').read_text());(P/'review/sentinel_neutral_manifest.json').write_text(json.dumps(m,indent=2)+'\n')
m.update(revision='sentinel_textured_v1',default_model='sentinel_a',model='hes_sentinel_a.glb')
m['models']=[]
for id,label,tier in [('sentinel_a','10055 Sentinel · ivory · ×1.0','a'),('sentinel_b','10056 Heavy Sentinel · scorched · ×1.2','b'),('sentinel_c','10057 Crown Sentinel · gilded · ×1.3','c'),('throne_turret','10144 Throne Turret · gilded · ×1.3','c')]:
 digest=sha(v/f'hes_sentinel_{tier}.glb');m['models'].append({'id':id,'label':label,'revision':'sentinel_textured_v1','url':f'hes_sentinel_{tier}.glb?v={digest[:12]}','sha256':digest,'runtime_sha256':sha(P/'export/hes_sentinel.glb')})
for clip in m['clips'].values():
 for a in clip['anchors']:a['source_images']=[f'../../references_hd/{n}/00_three_quarter.png' for n in ['sentinel','heavy_sentinel','crown_sentinel']]
(v/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
f=v/'index.html';s=f.read_text().replace('Hesper Sentinel — neutral rig','Hesper Sentinels and Throne Turret').replace('Five clips; neutral grey while the shared texture job is pending.','Ivory, scorched and gilded finishes; five animation clips.').replace('Shared neutral geometry for all four Sentinel rows. Tier colours await the texture return.','Viewer copies bake the shared runtime ramps. Labels show game scale; the viewer uses a common comparison size.').replace('Loading the neutral rig…','Loading the textured Sentinel…');f.write_text(s)
# Comparison sheet and LOD result summary for the integrator.
sheet=Image.new('RGB',(1500,500),(55,55,55));draw=ImageDraw.Draw(sheet)
for i,t in enumerate('abc'):
 im=Image.open(P/f'review/sentinel_geometry/pbr_{t}_Standing.png').convert('RGB').resize((500,500));sheet.paste(im,(i*500,0));draw.text((i*500+15,15),['A — Ivory','B — Scorched','C / Throne — Gilded'][i],fill='white')
sheet.save(P/'review/sentinel_tiers.png')
rows=list(csv.DictReader((P/'review/sentinel_tier_lods/scores.tsv').open(),delimiter='\t'));result={}
for tier in 'abc':
 r={int(x['lod']):x for x in rows if x['model']=='hes_sentinel_'+tier}
 assert float(r[2]['outline_pct'])<=6 and float(r[2]['colour_diff'])<=max(16,float(r[1]['colour_diff'])+3)
 assert float(r[3]['outline_pct'])<=13 and float(r[3]['colour_diff'])<=19.5
 result[tier]={'passed':True,'scores':r,'lod2_colour_limit':max(16,float(r[1]['colour_diff'])+3)}
(P/'review/sentinel_tier_lods/result.json').write_text(json.dumps(result,indent=2)+'\n')
print('Four-row viewer and passing tier LOD summary ready.')
