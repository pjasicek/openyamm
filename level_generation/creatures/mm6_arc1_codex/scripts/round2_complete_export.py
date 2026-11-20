import runpy,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
def plain(name):subprocess.run(['/usr/bin/python3',str(P/'scripts'/name)],check=True)
plain('round2_skin_gate.py')
for name in ['round2_assemble.py','round2_lod_gates.py','round2_head_probe.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
plain('round2_pack_lods.py');plain('pack_runtime.py')
for name in ['round2_material_metrics.py','round2_endchecks.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
