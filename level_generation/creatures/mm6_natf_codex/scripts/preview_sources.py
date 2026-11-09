"""Source-only G1 evidence; reuses the bar1 mannequin preview and ROM scripts."""
import json
import runpy
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[1]
root = project.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(project.parent / 'mm6_bar1_claude/scripts'))
roles = json.loads((project / 'source/motion_candidates.json').read_text())
groups = {}
for candidate in roles.values():
    groups.setdefault(candidate['files']['in_place_glb'], []).append(candidate['glb_clip'])
for source, clips in groups.items():
    for view in ('front', 'left', 'three_quarter'):
        output = project / 'review/g1' / Path(source).stem / view
        sys.argv = ['rpg_preview.py', '--', str(root / source), str(output), view, '5', *clips]
        runpy.run_path(str(project / 'scripts/rpg_preview.py'), run_name='__main__')
        rows = json.loads((output / 'frames.json').read_text())
        assert len(rows) == len(clips) and all(len(row) == 5 for row in rows)
sys.argv = ['rom_extract.py', '--', *[
    f"{role}={root / candidate['files']['in_place_glb']}:{candidate['glb_clip']}"
    for role, candidate in roles.items()]]
runpy.run_path(str(project / 'scripts/rom_extract.py'), run_name='__main__')
assert len(json.loads((project / 'work/rom.json').read_text())['roles']) == len(roles)
print('Source-only G1 preview/ROM complete. No creature rig or prop gate is claimed.')
