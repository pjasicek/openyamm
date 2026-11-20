import bpy,sys,os,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from gates_summary import summarize
allg={}
for level in range(4):
 os.environ['MFP_LEVEL']=str(level);runpy.run_path(str(P/'scripts/export_reimport.py'),run_name='__main__')
 os.environ.update(GATE_BLEND=str(P/f'work/export_reimport_lod{level}.blend'),GATE_REPORT=str(P/f'review/export_lod{level}_gates.json'),GATE_RENDER='0')
 runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');gate=summarize(json.loads(Path(os.environ['GATE_REPORT']).read_text()));allg[str(level)]=gate;print('EXPORTED_GATE',level,gate,flush=True)
(P/'review/export_gates_summary.json').write_text(json.dumps(allg,indent=2))
runpy.run_path(str(P/'scripts/motion_proof.py'),run_name='__main__')
for level in range(4):
 os.environ.update(EXTRA_BLEND=str(P/f'work/export_reimport_lod{level}.blend'),EXTRA_REPORT=str(P/f'review/export_prop_lod{level}.json'))
 runpy.run_path(str(P/'scripts/extra_metrics.py'),run_name='__main__')
 assert json.loads(Path(os.environ['EXTRA_REPORT']).read_text())['blade_contact_mm']<=2
proof=json.loads((P/'review/motion_proof.json').read_text());assert not any(row['smoothness_flags']for row in proof['clips'].values()),'angular smoothness'
sys.argv=['g4_weights.py','--',str(P/'work/export_reimport_lod0.blend'),'export','Standing:0','Walking:10','Running:8','Attack:13','Attack:23','Hit:5','Death:30','Death:60','Dead:0','Fidget:30']
runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
assert all(x['pass']for x in allg.values()),allg
