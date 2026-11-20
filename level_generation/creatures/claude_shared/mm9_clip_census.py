#!/usr/bin/env python3
"""MM9 source clips against an installed GLB's clips (dropped-clip pass, 2026-10-31).

    mm9_clip_census.py <ABC name or path> <installed.glb> [more ABCs ...]

Prints the source clip names (bind poses marked), each clip's key count and length, and the installed clip names.
Mapping derived clips (Running = walk x1.5, a stitched Death) back to their source is the caller's job.
"""
import json
from pathlib import Path
import struct
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
import convert_abc_model as C  # noqa: E402


def abc_path(name):
    path = Path(name)
    if path.exists():
        return path
    return REPO / 'mm9/extracted/MODELS/MODELS' / (name if name.lower().endswith('.abc') else name + '.abc')


def glb_clips(path):
    data = Path(path).read_bytes()
    length = struct.unpack('<I', data[12:16])[0]
    document = json.loads(data[20:20 + length])
    return [a.get('name') for a in document.get('animations', [])]


def main():
    *abcs, glb = sys.argv[1:]
    for name in abcs:
        model = C.read_abc(abc_path(name))
        print(f'{abc_path(name).name}: {len(model.animations)} animations')
        for animation in model.animations:
            keys = animation.keyframes
            length = (keys[-1].time_ms - keys[0].time_ms) / 1000 if keys else 0
            events = [k.event for k in keys if k.event]
            print(f'  {animation.name:20s} keys {len(keys):3d} {length:6.3f} s {" ".join(events)[:80]}')
    print(f'{Path(glb).name}: {", ".join(glb_clips(glb))}')


if __name__ == '__main__':
    main()
