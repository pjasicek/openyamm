#!/usr/bin/env python3
"""Add script_clips to every MM9 descriptor that uses a model (dropped-clip pass, run2-clips-groupC, 2026-10-31).

    bind_script_clips.py <model file name, e.g. mm9_dfly.glb> role=Clip [role=Clip ...] [--dry-run] [--replace]

Takes the flock claude_shared/locks/mm9_actors_yml.lock itself, re-reads assets_dev/worlds/mm9/models/actors.yml
inside it, and in each `- descriptor:` entry whose `model:` ends with the file name adds the roles to its
`script_clips:` block (created at the end of the entry when missing; existing roles are kept unless --replace).
Comments and every other line stay as they are. Writes via temp + rename (the file is hard-linked into output/).
"""
import fcntl
import os
from pathlib import Path
import re
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
ACTORS = REPO / 'assets_dev/worlds/mm9/models/actors.yml'
LOCK = Path(__file__).resolve().parent / 'locks/mm9_actors_yml.lock'


def bind(lines, model, roles, replace=False):
    starts = [i for i, l in enumerate(lines) if l.startswith('- descriptor:')]
    changed, out_desc = 0, []
    for k in reversed(range(len(starts))):
        a = starts[k]
        b = starts[k + 1] if k + 1 < len(starts) else len(lines)
        # the entry ends at its last indented line (trailing comments belong to the next entry)
        end = a
        for i in range(a + 1, b):
            if lines[i].startswith('  ') or lines[i].strip() == '':
                if lines[i].strip():
                    end = i
            elif lines[i].startswith('- '):
                break
            elif lines[i].startswith('#'):
                # a top-level comment ends the entry when only comments/blank follow up to b
                if all(not x.strip() or x.startswith('#') for x in lines[i:b]):
                    break
        block = lines[a:end + 1]
        if not any(re.match(r'\s+model:\s*\S*' + re.escape(model) + r'\s*$', l) for l in block):
            continue
        out_desc.append(lines[a].split(':', 1)[1].strip())
        sc = next((i for i in range(a, end + 1) if lines[i].rstrip() == '  script_clips:'), None)
        if sc is None:
            new = ['  script_clips:'] + [f'    {r}: {c}' for r, c in roles]
            lines[end + 1:end + 1] = new
            changed += 1
            continue
        last = sc
        have = {}
        for i in range(sc + 1, end + 1):
            m = re.match(r'    (\w+):\s*(\S+)', lines[i])
            if not m:
                break
            have[m.group(1)] = m.group(2)
            last = i
        for r, c in roles:
            if r in have and have[r] != c:
                if replace:
                    i = next(i for i in range(sc + 1, last + 1) if re.match(r'    ' + r + r':', lines[i]))
                    lines[i] = f'    {r}: {c}'
                    changed += 1
                else:
                    print(f'  kept existing {r}: {have[r]} (wanted {c})')
        add = [f'    {r}: {c}' for r, c in roles if r not in have]
        if add:
            lines[last + 1:last + 1] = add
            changed += 1
    return changed, list(reversed(out_desc))


def main():
    args = [a for a in sys.argv[1:] if a not in ('--dry-run', '--replace')]
    model, pairs = args[0], [tuple(p.split('=', 1)) for p in args[1:]]
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        text = ACTORS.read_text()
        lines = text.split('\n')
        changed, descs = bind(lines, model, pairs, '--replace' in sys.argv)
        print(f'{model}: {len(descs)} descriptors ({"; ".join(descs)}), {changed} changed')
        if '--dry-run' in sys.argv or not changed:
            return
        fd, tmp = tempfile.mkstemp(dir=ACTORS.parent, prefix='.actors_', suffix='.yml')
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join(lines))
        os.chmod(tmp, ACTORS.stat().st_mode & 0o777)
        os.replace(tmp, ACTORS)


if __name__ == '__main__':
    main()
