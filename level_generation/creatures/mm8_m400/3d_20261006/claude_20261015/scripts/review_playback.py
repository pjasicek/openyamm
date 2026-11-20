import subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1]
url='http://127.0.0.1:8765/'+str(p.relative_to(p.parents[4]))+'/review/viewer/'
subprocess.run(['node',str(p.parent/'review_playback.mjs'),url,str(p/'review/playback')],check=True)
