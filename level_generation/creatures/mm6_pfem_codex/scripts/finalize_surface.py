import runpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/surface_crossings.py'),run_name='__main__')
d=json.loads((p/'work/surface_crossings.json').read_text())
assert not any(d.values()), d
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
