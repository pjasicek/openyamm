from pathlib import Path
import json,datetime
from PIL import Image
from process import ROOT,queue,save
art=Image.open(ROOT/'cleaned/m528wa0.png').convert('RGBA');bg=Image.new('RGBA',art.size,(255,0,255,255));bg.alpha_composite(art)
p=ROOT/'checkpoints/accepted_identity_v1.png'
assert not p.exists(),'Accepted reference is immutable'
bg.convert('RGB').save(p)
record={'status':'accepted_identity_only','frame':'m528wa0','raw':'raw/identity_v3.png','reference':'checkpoints/accepted_identity_v1.png','review':['review/identity_native_restored.png','review/identity_edges.png'],'decision':'Native pose, placement, smoky core, central streak and pale gold-white electrical wisps retained. Enlarged pixel blocks and repeated orange starbursts rejected in earlier attempts. Locally repaired warm filament edge contamination confirmed clean on light and dark backgrounds. Fine filament reconstruction is interpretive; native appearance and tonal balance remain recognizable.','palette':528,'variants':'All three native descriptors use palette 528; no recolor regions, exact shared base, native scale and glow-radius differences retained.','processing_sha256':queue.sha(ROOT/'processing.json'),'raw_sha256':queue.sha(ROOT/'raw/identity_v3.png'),'reference_sha256':queue.sha(p),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(ROOT/'checkpoints/identity_acceptance.json',record)
g=json.loads((ROOT/'generation.json').read_text());g['batches']['identity']['references']=[{'path':r,'sha256':queue.sha(ROOT/r)} for r in ['raw/identity_v2.png','references/identity_matte.png']];g['batches']['identity']['status']='accepted_identity';save(ROOT/'generation.json',g)
b=json.loads((ROOT/'batches.json').read_text());b['identity']['state']='accepted_identity';save(ROOT/'batches.json',b)
for key in b:
 if key=='identity':continue
 text=(ROOT/f'prompts/{key}_v1.txt').read_text();text+='Reconstruct fine smoky and electrical detail rather than enlarged square pixel blocks. Electricity must remain pale ivory-white with faint desaturated straw-gold edges: no saturated orange or red, repetitive star shapes, opaque circular halo or enlarged core. Keep each native frame\'s individual shape and changing brightness exactly; do not replace the sequence with duplicates of input 2.\n'
 (ROOT/f'prompts/{key}_v2.txt').write_text(text)
p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['families']['m528']['resume']='Accepted identity is checkpoints/accepted_identity_v1.png. Generate pending nonidentity batches using references/{batch}_matte.png and that accepted identity with prompts/{batch}_v2.txt. Process each; then export and validate all 56 frames with native scale/glow/Center/Lit data.';p.write_text(json.dumps(ledger,indent=2)+'\n')
print('Identity accepted; 9 native action batches ready, single native palette 528.')
