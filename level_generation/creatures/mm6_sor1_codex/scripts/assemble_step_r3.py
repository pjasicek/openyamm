from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1]
for script in ['merge_lods_r3.py','assemble_runtime_r3.py','audit_runtime.py']:
 r=subprocess.run(['/usr/bin/python3',str(p/'scripts'/script)],capture_output=True,text=True);(p/'work'/f'{script}.log').write_text(r.stdout+r.stderr);assert r.returncode==0,(script,r.stderr)
print('ASSEMBLED AND AUDITED',flush=True)
