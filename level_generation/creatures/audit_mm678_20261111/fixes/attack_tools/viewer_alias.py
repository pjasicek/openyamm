#!/usr/bin/env python3
"""Review viewer only: give the "before" models a clip under the new clip's name, as a copy of the clip the binding
played in that slot before (attacks stream, 2026-11-11), so the viewer loads every revision and the before/after
switch compares the attack slot. Updates the manifest's sha256 and url for each changed model.

    viewer_alias.py <project>/review/viewer Attack=Cast [Cast=Attack ...]
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def main():
    viewer = Path(sys.argv[1])
    pairs = [a.split('=') for a in sys.argv[2:]]
    manifest = json.loads((viewer / 'manifest.json').read_text())
    for model in manifest['models']:
        if not model['id'].endswith('_before'):
            continue
        path = viewer / model['url'].split('?')[0]
        glb = glb_pose.Glb(path)
        names = [a.get('name') for a in glb.json['animations']]
        changed = False
        for new, old in pairs:
            if new not in names and old in names:
                clip = copy.deepcopy(glb.json['animations'][names.index(old)])
                clip['name'] = new
                glb.json['animations'].append(clip)
                changed = True
        if changed:
            glb.write(path)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            model['sha256'] = sha
            model['url'] = f"{path.name}?v={sha[:12]}"
            print('aliased', path.name)
    (viewer / 'manifest.json').write_text(json.dumps(manifest, indent=1))


if __name__ == '__main__':
    main()
