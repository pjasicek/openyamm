"""Verify only the assigned models and their scoped desktop cook receipts."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
owned=json.loads((P/'ownership.json').read_text());receipts=json.loads((P/'install_receipts.json').read_text())
rows={};assert len(owned)==69
with (P/'review/cook_verify.log').open('w') as log:
    for row in owned:
        icon=row['icon'];source=R/'assets_source/engine/world_items/models'/f'item_{icon}.glb'
        runtime=R/'assets_dev/engine/world_items/models'/f'item_{icon}.glb'
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        assert sha(source)==receipts[icon]['source_sha256'],(icon,'source differs from reviewed export')
        assert sha(runtime)==receipts[icon]['runtime_sha256'],(icon,'runtime changed')
        result=subprocess.run([sys.executable,str(R/'tools/cook_models.py'),'--verify','--profile','desktop',
            '--only',f'engine/world_items/models/item_{icon}.glb'],stdout=log,stderr=subprocess.STDOUT)
        assert result.returncode==0,(icon,'scoped cook failed; see cook_verify.log')
        rows[icon]={'verified':True,'source_sha256':sha(source),'runtime_sha256':sha(runtime)}
        print('VERIFIED',icon,flush=True)
(P/'review/cook_verification.json').write_text(json.dumps({'count':len(rows),'icons':rows},indent=2)+'\n')
assert len(rows)==69
