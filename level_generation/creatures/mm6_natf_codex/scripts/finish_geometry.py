import bpy,json,sys,runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import equipped_reduction as eq,candidate_gates as gates
sel=json.loads((P/'review/reduction_selected.json').read_text());path=P/'review/final/reduction.json';report=json.loads(path.read_text())
for level in [1,2,3]:
 row=eq.trial(level,'final',{n:sel[n][str(level)]for n in sel});report[str(level)]=row;path.write_text(json.dumps(report,indent=2));assert row['pass'],level
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
path=P/'review/final/all_gates.json';results=json.loads(path.read_text())
for level in [1,2,3]:
 results[str(level)]=gates.run(P/f'work/final_lod{level}.blend',f'lod{level}');path.write_text(json.dumps(results,indent=2));assert results[str(level)]['pass'],level
runpy.run_path(str(P/'scripts/contact_motion.py'),run_name='__main__')
d=json.loads((P/'review/final/grip_contact.json').read_text());assert max(r['palm_gap_max_mm']for level in d.values()for r in level.values())<=3
runpy.run_path(str(P/'scripts/final_sheets.py'),run_name='__main__')
for script in ['finalize_runtime.py','viewer_tiers.py','strict_runtime_check.py']:subprocess.run(['/usr/bin/python3',str(P/'scripts'/script)],check=True)
print('FINAL_GEOMETRY_PACKAGE_PASS',flush=True)
