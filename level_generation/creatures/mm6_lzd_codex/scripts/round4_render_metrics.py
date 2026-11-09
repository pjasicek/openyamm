import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
import subprocess
subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_tiers.py'),'final0','round4_shared'],check=True)
chosen=json.loads((P/'review/round4/lod_selection.json').read_text())
for level in range(4):
 reference=P/'work/round4/repaired.blend'if level==0 else P/'work/round4/near_runtime.blend';palette='final0'if level==0 else 'round4_shared'
 render(reference,'r4_reference',level,palette=(palette,'lzd_a'),parts=('body','bow')if level==0 else('actor',),samples=32,camera_path=P/'review/round4/camera.json')
 render(P/chosen[str(level)]['blend'],'r4_candidate',level,palette=('round4_shared','lzd_a'),parts=('body','bow')if level==0 else('actor',),samples=32,camera_path=P/'review/round4/camera.json')
