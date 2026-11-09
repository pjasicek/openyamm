from pathlib import Path
import json, hashlib, datetime
R=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256((R/p).read_bytes()).hexdigest()
def entry(p): return {'path':p,'sha256':sha(p)}
def save(p,d): (R/p).write_text(json.dumps(d,indent=2)+'\n')
attempts=[]
for version,refs,status,reason in [
 (1,['references/identity_matte.png'],'rejected','Enlarged native pixel blocks remained.'),
 (2,['raw/identity_v1.png'],'rejected','Restored electrical filaments were too orange and repeatedly star-shaped compared with native pale gold-white wisps.'),
 (3,['raw/identity_v2.png','references/identity_matte.png'],'processed_unreviewed','Corrected pale gold-white filaments; native/restored comparison inspected. Full edge and tonal-weight acceptance is still pending before using this as the action reference.')]:
 attempts.append({'version':version,'tool':'built-in image_gen','raw':entry(f'raw/identity_v{version}.png'),'prompt':entry(f'prompts/identity_v{version}.txt'),'references':[entry(p) for p in refs],'status':status,'reason':reason})
save('checkpoints/generation_attempts.json',{'attempts':attempts})
g=json.loads((R/'generation.json').read_text());g['batches']['identity']['references']=attempts[-1]['references'];save('generation.json',g)
p=R.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text())
ledger['families']['m528']['resume']='Identity v3 is processed but not accepted. Review review/identity_native_restored.png and light/dark edge composites, correct any remaining native color/tonal-weight mismatch, then seal an accepted identity reference. Generate the 9 remaining batches from their exact native references and accepted identity. Run process.py per batch, export all 56 native frames, preserve Center/Lit/glow_radius and descriptor scales, validate animation/variants/edges, seal acceptance and refresh inventory. All 3 identity attempts and exact input hashes are in checkpoints/generation_attempts.json.'
ledger['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p.write_text(json.dumps(ledger,indent=2)+'\n')
print('Preserved all three identity attempts, repaired v3 input provenance and recorded exact resume steps.')
