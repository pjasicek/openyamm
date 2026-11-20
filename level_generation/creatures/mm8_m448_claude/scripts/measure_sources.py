"""Retain source frames and ROM extremes before fitting the Ratman rig."""
from pathlib import Path
import json
import runpy
import sys
p = Path(__file__).resolve().parents[1]
repo = p.parents[2]
def run(name, *args):
    script = p / 'scripts' / name
    sys.argv = [str(script), '--', *map(str, args)]
    runpy.run_path(str(script), run_name='__main__')
source = repo / 'anim_library/humanoid_set/Armed.glb'
run('source_rest.py', source)
f = p / 'work/source_rest.json'
d = json.loads(f.read_text())
d = {k:v for k,v in d.items() if '_Finger3' not in k}
assert all(not v['child'] or v['child'] in d for v in d.values())
f.write_text(json.dumps(d, indent=2)+'\n')
run('proportions.py', 'source', source)
clips = json.loads((p / 'creature_3d_progress.json').read_text())['motion']['selected_source_clips']
run('rom_extract.py', *[c['role']+'='+str(repo/c['source_file'])+':'+c['source_clip'] for c in clips])
