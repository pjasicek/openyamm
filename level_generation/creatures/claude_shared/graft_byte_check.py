#!/usr/bin/env python3
"""After graft_clips.py: is the grafted GLB the old one plus clips only? (dropped-clip pass, 2026-10-31)

    graft_byte_check.py <before.glb> <after.glb>

Checks: the old binary chunk is a byte prefix of the new one; every old accessor, bufferView, mesh, node, skin,
material, texture, image and extension entry is unchanged; the old animations are unchanged and first, in order.
Prints the added clips and the size change, and exits 1 on any difference.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'floor'))
import glb_pose  # noqa: E402


def main():
    a, b = glb_pose.Glb(sys.argv[1]), glb_pose.Glb(sys.argv[2])
    problems = []
    if bytes(b.bin[:len(a.bin)]) != bytes(a.bin):
        problems.append('old buffer is not a prefix')
    for key in sorted(set(a.json) | set(b.json)):
        if key in ('buffers',):
            continue
        old, new = a.json.get(key), b.json.get(key)
        if isinstance(old, list):
            if new[:len(old)] != old:
                problems.append(f'{key}: old entries changed')
        elif old != new:
            problems.append(f'{key} changed')
    added = [x.get('name') for x in b.json.get('animations', [])[len(a.json.get('animations', [])):]]
    size_a, size_b = Path(sys.argv[1]).stat().st_size, Path(sys.argv[2]).stat().st_size
    print(f'added {len(added)} clips: {", ".join(added)}; {size_a / 1e6:.2f} -> {size_b / 1e6:.2f} MB')
    print('OK' if not problems else 'DIFFERS: ' + '; '.join(problems))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
