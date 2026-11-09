"""Preserve owned baselines and make readable source-icon boards before authoring weapons."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];R=P.parents[2]
rows=json.loads((P/'ownership.json').read_text());assert len(rows)==69 and len({r['icon'] for r in rows})==69
out=P/'review';out.mkdir(exist_ok=True);baseline=P/'baseline';baseline.mkdir(exist_ok=True)
hashes={}
for row in rows:
 icon=row['icon'];source=R/'assets_source'/row['binding']['model'];destination=baseline/source.name
 if not destination.exists():shutil.copyfile(source,destination)
 hashes[icon]=hashlib.sha256(destination.read_bytes()).hexdigest()
for family in ['daggers','axes']:
 subset=[r for r in rows if r['family']==family]
 for start in range(0,len(subset),20):
  board=Image.new('RGB',(1600,1200),(42,44,48));draw=ImageDraw.Draw(board)
  for n,row in enumerate(subset[start:start+20]):
   x=n%5*320;y=n//5*300;draw.text((x+5,y+4),row['icon']+' '+row['items'][0]['name'],fill='white')
   im=Image.open(R/row['icon_reference']).convert('RGBA');im.thumbnail((300,270));board.paste(im,(x+(320-im.width)//2,y+25+(270-im.height)//2),im)
  board.save(out/f'icons_{family}_{start//20+1}.png')
(out/'baseline_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
ledger=P/'ledger.json'
if not ledger.exists():ledger.write_text(json.dumps([{'icon':r['icon'],'family':r['family'],'name':r['items'][0]['name'],'status':'pending','length':r['binding']['length'],'baseline':str((baseline/('item_'+r['icon']+'.glb')).relative_to(P)),'remaining_defects':['Audited relief: rebuild physical components and PBR.']} for r in rows],indent=2)+'\n')
print('Preserved',len(hashes),'baselines; four icon boards.')
