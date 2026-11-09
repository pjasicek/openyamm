"""Select an unaccepted identity revision, preserving the superseded attempt."""
import json,shutil
from process import ROOT,run,save
checkpoint=ROOT/'checkpoints/identity_v1_processing';checkpoint.mkdir(exist_ok=True)
for name in ['tone_settings.json','processing.json','registration.json','generation.json']:
 p=ROOT/name
 if p.exists():shutil.copyfile(p,checkpoint/name)
(ROOT/'tone_settings.json').unlink()
run('identity','identity_v2.png','identity_v2.txt')
save(ROOT/'checkpoints/generation_attempts.json',{'rejected':[{'raw':'raw/identity_v1.png','prompt':'prompts/identity_v1.txt','reason':'Enlarged figure silhouettes, simplified blocky material treatment and too-bright flippers. Replaced by identity_v2, subject to final review.'}],'selected_identity':'raw/identity_v2.png','status':'unreviewed'})
