"""Preserve identity v2 before selecting the material-refined identity v3."""
import json,shutil
from process import ROOT,run,save,queue
checkpoint=ROOT/'checkpoints/identity_v2_processing';assert not checkpoint.exists();checkpoint.mkdir()
for name in ['tone_settings.json','processing.json','registration.json','generation.json']:
 p=ROOT/name
 if p.exists():shutil.copyfile(p,checkpoint/name)
(ROOT/'tone_settings.json').unlink()
run('identity','identity_v3.png','identity_v3.txt',identity='raw/identity_material_v1.png')
p=ROOT/'checkpoints/generation_attempts.json';g=json.loads(p.read_text());g['rejected'].append({'raw':'raw/identity_v2.png','prompt':'prompts/identity_v2.txt','reason':'Improved native sizing, but flat polygonal material treatment remained. Superseded by v3 with focused material reference.'});g['selected_identity']='raw/identity_v3.png';g['material_reference']={'raw':'raw/identity_material_v1.png','prompt':'prompts/identity_material_v1.txt','reference':'references/identity_material_native.png','role':'Focused shell/skin detail reference only; native multi-view input controls final poses.','hashes':{n:queue.sha(ROOT/n) for n in ['raw/identity_material_v1.png','prompts/identity_material_v1.txt','references/identity_material_native.png']}};save(p,g)
