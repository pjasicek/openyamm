"""Install only explicitly reviewed owned exports, preserving baseline collisions."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
R=P.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
owned={x['icon']:x for x in json.loads((P/'ownership.json').read_text())}
ledger=json.loads((P/'ledger.json').read_text())
for icon in sys.argv[1:]:
    entry=owned[icon];source=R/'assets_source'/entry['model'];runtime=R/'assets_dev'/entry['model']
    assert sha(source)==ledger[icon].get('source_sha256',entry['baseline_source_sha256']),(icon,'source collision')
    assert sha(runtime)==ledger[icon].get('runtime_sha256',entry['baseline_runtime_sha256']),(icon,'runtime collision')
    export=P/f'work/codex_tex/geometryfinish_{icon}_export.glb'
    acceptance=json.loads((P/f'review/{icon}_acceptance.json').read_text())
    assert acceptance['accepted'] and acceptance['export_sha256']==sha(export)
    subprocess.run([sys.executable,str(R/'tools/install_model.py'),str(export),'--world-items','--name',Path(entry['model']).name],check=True)
    assert sha(source)==sha(export)
    subprocess.run([sys.executable,str(R/'tools/cook_models.py'),'--verify','--profile','desktop','--only',entry['model']],check=True)
    ledger[icon].update(status='installed_pending_native',installed=True,export_sha256=sha(export),source_sha256=sha(source),runtime_sha256=sha(runtime),acceptance=str(P/f'review/{icon}_acceptance.json'))
    (P/'ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print('INSTALLED',icon)
