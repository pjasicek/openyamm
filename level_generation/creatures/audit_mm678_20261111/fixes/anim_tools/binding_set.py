#!/usr/bin/env python3
"""Set binding keys in a world's actors.yml for every descriptor of one model (anim-stream fixes, 2026-11-11).

    binding_set.py --world mm6 --model mm6_mfp.glb animation.run_stride_length=2.05 \
        'animation.events.attack_melee={impact: 0.61}' clips.cast=Cast [--descriptors 'Ogre Mage A,Ogre Mage B'] [--dry]

Line-based, so comments and layout stay: inside each `- descriptor:` entry whose `model:` is the given file, the line
of the dotted key (two-space indent per level) gets the new value; a missing key is inserted as the first child of its
parent block (the parent must exist). The file is written to a temporary file and renamed over actors.yml: the
assets_dev files are hard links shared with review mirrors and must not be edited in place. Prints every change.
"""
import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def entries(lines):
    starts = [i for i, line in enumerate(lines) if line.startswith('- descriptor:')]
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(lines)
        # an entry ends at the first non-indented, non-blank line after its start (comments of the next entry)
        for i in range(s + 1, e):
            if lines[i].strip() and not lines[i].startswith(' '):
                e = i
                break
        yield s, e


def find_key(lines, s, e, path):
    """Index of the line of a dotted key inside entry [s, e) (top-level keys at indent 2), or (parent index, None)."""
    indent, lo, hi = 2, s, e
    parent = None
    for depth, key in enumerate(path):
        pat = re.compile(r'^' + ' ' * indent + re.escape(key) + r':(\s|$)')
        hit = None
        for i in range(lo if depth else s, hi):
            if pat.match(lines[i]) or (depth == 0 and lines[i].startswith('- ' + key + ':')):
                hit = i
                break
        if hit is None:
            return parent, None, indent
        if depth == len(path) - 1:
            return parent, hit, indent
        parent = hit
        lo = hit + 1
        hi = lo
        while hi < e and (not lines[hi].strip() or len(lines[hi]) - len(lines[hi].lstrip()) > indent):
            hi += 1
        indent += 2
    return parent, None, indent


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--world', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--descriptors')
    p.add_argument('--dry', action='store_true')
    p.add_argument('sets', nargs='+')
    args = p.parse_args()
    path = ROOT / f'assets_dev/worlds/{args.world}/models/actors.yml'
    lines = path.read_text().split('\n')
    only = set(d.strip() for d in args.descriptors.split(',')) if args.descriptors else None
    changes = 0
    for s, e in reversed(list(entries(lines))):
        block = lines[s:e]
        name = block[0].split(':', 1)[1].strip()
        if not any(re.match(r'^  model: worlds/' + re.escape(args.world) + r'/models/' + re.escape(args.model) + r'\s*$',
                            line) for line in block):
            continue
        if only is not None and name not in only:
            continue
        for item in args.sets:
            key, value = item.split('=', 1)
            keys = key.split('.')
            parent, hit, indent = find_key(lines, s, e, keys)
            new = ' ' * indent + keys[-1] + ': ' + value
            if hit is not None:
                if lines[hit] != new:
                    print(f'{name}: {lines[hit].strip()} -> {new.strip()}')
                    lines[hit] = new
                    changes += 1
            elif parent is not None or len(keys) == 1:
                at = (parent + 1) if parent is not None else s + 1
                print(f'{name}: + {new.strip()}')
                lines.insert(at, new)
                e += 1
                changes += 1
            else:
                sys.exit(f'{name}: no parent block for {key}')
    print(f'{changes} changes')
    if args.dry or not changes:
        return
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.actors.', suffix='.yml')
    with os.fdopen(fd, 'w') as f:
        f.write('\n'.join(lines))
    os.chmod(tmp, path.stat().st_mode & 0o777)
    os.replace(tmp, path)


if __name__ == '__main__':
    main()
