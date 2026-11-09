"""Install only the individually reviewed ownership list, then verify each exact cooked file."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

P=Path(__file__).resolve().parents[1]
ROOT=P.parents[2]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    state=json.loads((P/'progress.json').read_text())
    rows=json.loads((P/'ownership.json').read_text());assert len(rows)==43
    only=set(sys.argv[1:]);assert only.issubset({r['icon'] for r in rows}),only
    if only:rows=[r for r in rows if r['icon'] in only]
    validation={Path(r['export']).name.removesuffix('_export.glb'):r for r in json.loads((P/'review/validation.json').read_text())}
    logs=P/('review/normal_pass/install_logs' if only else 'review/install_logs');logs.mkdir(exist_ok=True)
    for row in rows:
        icon=row['icon'];record=state['icons'][icon];checked=validation[icon]
        source=ROOT/'assets_source/engine/world_items/models'/f'item_{icon}.glb'
        export=P/checked['export'];assert digest(export)==checked['sha256']
        assert record['status'] in ['ready','installed'],(icon,record['status'])
        assert digest(source) in [record['baseline_source_sha256'],record.get('source_sha256'),checked['sha256']],(icon,'unexpected source edit')
        relative=f'engine/world_items/models/item_{icon}.glb'
        commands=[[sys.executable,'tools/install_model.py',str(export),'--world-items','--name',f'item_{icon}.glb'],
                  [sys.executable,'tools/cook_models.py','--verify','--profile','desktop','--only',relative]]
        for n,command in enumerate(commands):
            result=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (logs/f'{icon}_{n}.log').write_text(result.stdout)
            assert result.returncode==0,(icon,command,result.stdout[-3000:])
        assert digest(source)==checked['sha256']
        record.update({'status':'installed','export':checked['export'],'source_sha256':digest(source),
                       'runtime_sha256':digest(ROOT/'assets_dev'/relative),'cooked_verified':True})
        (P/'progress.json').write_text(json.dumps(state,indent=2)+'\n')
        print('INSTALLED + VERIFIED',icon,flush=True)


if __name__=='__main__':main()
