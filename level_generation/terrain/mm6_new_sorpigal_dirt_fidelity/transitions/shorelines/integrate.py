"""Install only terrain and prove that all other existing playtest files remain unchanged."""
import json
import os
import subprocess
from pathlib import Path
from build import P, ROOT, sha


def inventory(stage, targets):
    result = {}
    for directory, dirs, files in os.walk(stage, followlinks=False):
        base = Path(directory)
        if base == stage:
            dirs[:] = [d for d in dirs if d != 'seed']
        for name in dirs + files:
            path = base / name
            relative = str(path.relative_to(stage))
            if relative in targets or relative == 'playtest_snapshot.json': continue
            if path.is_symlink(): result[relative] = {'symlink': os.readlink(path)}
            elif path.is_file(): result[relative] = sha(path)
    return result


def main():
    stage = Path('/tmp/openyamm-sorpigal-peasants-playtest')
    files = json.loads((P / 'report.json').read_text())['files']
    targets = {'enhanced/assets_dev/worlds/mm6/terrain_x2/' + n for n in files}
    previous_terrain = {n: sha(stage / 'enhanced/assets_dev/worlds/mm6/terrain_x2' / n) for n in files}
    before = inventory(stage, targets)
    snapshot = json.loads((stage / 'playtest_snapshot.json').read_text())
    subprocess.run(['python3', str(ROOT / 'level_generation/creatures/mm6_peasants/prepare_playtest.py'),
                    '--terrain-only'], check=True, cwd=ROOT)
    after = inventory(stage, targets)
    assert before == after, 'Non-terrain content changed'
    current = json.loads((stage / 'playtest_snapshot.json').read_text())
    for key in snapshot:
        if key not in ('terrain', 'water'): assert current[key] == snapshot[key], key
    for n, digest in files.items():
        assert sha(stage / 'enhanced/assets_dev/worlds/mm6/terrain_x2' / n) == digest
    changed = [n for n, h in files.items() if previous_terrain[n] != h]
    report = dict(passed=True, stage=str(stage), installed_files=files, changed_terrain=changed,
                  protected_entry_count=len(before), protected_entries=before,
                  other_snapshot_sections_unchanged=True,
                  exclusions=['63 enhanced terrain PNGs', 'terrain/water snapshot metadata', 'seed backups'],
                  note='Settings, executable, saves, maps, scene overlays, other art and symlink mounts unchanged.')
    (P / 'integration.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Preserved', len(before), 'non-terrain file hashes/symlink targets; installed', len(files), 'tiles.')

if __name__ == '__main__': main()
