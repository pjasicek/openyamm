from pathlib import Path
p=Path(__file__).resolve().parents[1];source=(p/'scripts/export_runtime.py').read_text()
source=source.replace("info={'clips':{},'lods':[]}","info=json.loads((out/'export_info.json').read_text());info['lods']=info['lods'][:1]").replace('for level in range(4):','for level in range(1,4):')
exec(compile(source,str(p/'scripts/export_runtime.py'),'exec'))
