"""Read-only exact-icon desktop verification; never cook or select another worker's models."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ownership=json.loads((PROJECT/'ownership.json').read_text())
    receipts=json.loads((PROJECT/'work/install_receipts.json').read_text())
    assert set(receipts)=={row['icon'] for row in ownership}
    result={};logs=[]
    for row in ownership:
        icon=row['icon'];relative=f'engine/world_items/models/item_{icon}.glb'
        expected=sha(PROJECT/f'work/exports/{icon}_export.glb')
        assert sha(ROOT/'assets_source'/relative)==receipts[icon]['source_sha256']==expected,icon
        assert sha(ROOT/'assets_dev'/relative)==receipts[icon]['runtime_sha256'],icon
        checked=subprocess.run([sys.executable,str(ROOT/'tools/cook_models.py'),'--verify','--profile','desktop',
                                '--only',relative],cwd=ROOT,text=True,capture_output=True,check=True)
        match=re.search(r'Verified (\d+) cooked models and (\d+) textures per profile: (\d+) problems',checked.stdout)
        assert match and int(match[1])==1 and int(match[3])==0,(icon,checked.stdout,checked.stderr)
        result[icon]={'models':1,'textures':int(match[2]),'problems':0,'source_sha256':expected,
                      'runtime_sha256':receipts[icon]['runtime_sha256']}
        logs.append(icon+': '+checked.stdout.strip())
        print('VERIFIED',icon,flush=True)
    (PROJECT/'work/cooked_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (PROJECT/'work/cooked_verification.txt').write_text('\n'.join(logs)+'\n9 exact owned models: zero problems.\n')
    print('9 installed source/runtime hashes and exact-model desktop cooks passed')


if __name__=='__main__':main()
