"""Shared viewer checker plus local appearance captures, with process-group cleanup."""
import subprocess,os,signal
from pathlib import Path
P=Path(__file__).resolve().parents[1]
url='http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/'
for script,log in [(P.parent/'claude_shared/check_viewer.mjs','check_viewer.log'),(P/'scripts/round5_capture_viewer.mjs','browser_capture.log')]:
 proc=subprocess.Popen(['node',str(script),url,'60'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
 try:
  output,_=proc.communicate(timeout=90);(P/'review'/log).write_text(output);print(output);assert proc.returncode==0,proc.returncode
 finally:
  try:os.killpg(proc.pid,signal.SIGTERM)
  except ProcessLookupError:pass
