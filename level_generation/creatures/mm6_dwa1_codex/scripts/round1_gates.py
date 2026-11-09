import runpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
start=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()
for name in ['exported_gates.py','skirt_intersections.py','uv_gate.py','extra_gates.py','render_final.py','render_lod_review.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
assert hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()==start
(P/'review/round1/gate_run.json').write_text(json.dumps({'final_sha256':start,'sample_hz':48,'gate_mesh':'LOD0 unchanged byte-for-byte; normalized reduced LODs verified separately','scripts':['exported_gates.py','skirt_intersections.py','uv_gate.py','extra_gates.py','render_final.py','render_lod_review.py']},indent=2))
