"""Install validated, visually reviewed potion exports one at a time through the shared lock."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import yaml

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owned=json.loads((PROJECT/'ownership.json').read_text())
    validated=json.loads((PROJECT/'receipts/validation.json').read_text())
    baseline=json.loads((PROJECT/'receipts/baseline.json').read_text())
    designs=json.loads((PROJECT/'designs.json').read_text())
    bindings={row['icon']:row for row in yaml.safe_load(
        (ROOT/'assets_dev/engine/world_items/items.yml').read_text())['items']}
    receipt_path=PROJECT/'receipts/install.json'
    receipts=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    assert len(validated)==41
    only=set(sys.argv[1:])
    for row in owned:
        icon=row['icon']
        if icon=='7item182' or (only and icon not in only):
            continue
        assert bindings[icon]['length']==designs['potions_'+icon]['length'], (icon,'binding differs from design')
        export=PROJECT/f'work/vessels/{icon}_export.glb'
        source=ROOT/f'assets_source/engine/world_items/models/item_{icon}.glb'
        runtime=ROOT/f'assets_dev/engine/world_items/models/item_{icon}.glb'
        assert sha(export)==validated[icon]['export_sha256'], (icon,'revalidate changed export')
        assert sha(source) in (baseline[icon]['source_sha256'],sha(export),
                               receipts.get(icon,{}).get('source_sha256')), (icon,'source changed outside this job')
        result=subprocess.run([sys.executable,str(ROOT/'tools/install_model.py'),str(export),'--world-items',
                               '--name',f'item_{icon}.glb'],cwd=ROOT,text=True,capture_output=True)
        (PROJECT/f'receipts/install_{icon}.log').write_text(result.stdout+result.stderr)
        if result.returncode:
            raise RuntimeError(f'{icon}: install failed; see receipts/install_{icon}.log')
        assert sha(source)==sha(export) and runtime.exists()
        doc=json.loads(runtime.read_bytes()[20:20+int.from_bytes(runtime.read_bytes()[12:16],'little')])
        for image in doc.get('images',[]):
            assert 'uri' in image and (runtime.parent/image['uri']).is_file(), (icon,image)
        receipts[icon]={'source_sha256':sha(source),'runtime_sha256':sha(runtime),
                        'binding_length':bindings[icon]['length'],
                        'installer':'tools/install_model.py --world-items','log':f'receipts/install_{icon}.log'}
        receipt_path.write_text(json.dumps(receipts,indent=2)+'\n')
        print('INSTALLED',icon,flush=True)
    print(f'Installed {len(receipts)} owned vessels; scroll untouched',flush=True)


if __name__=='__main__':
    main()
