#!/usr/bin/env python3
"""Dump what a Xeen .m song holds beyond the AdLib data: instrument definitions (all 26 bytes), SysEx blocks,
program changes, controllers, and per channel the note range, count and velocities."""
import sys
from collections import defaultdict
from pathlib import Path

d = Path(sys.argv[1]).read_bytes()
pos, stack, seen_loop = 0, [], False
info = defaultdict(lambda: {"notes": 0, "lo": 999, "hi": -1, "vel": set(), "prog": [], "ctl": set()})
other = defaultdict(int)
instr = {}
sysex = []
steps = 0
while steps < 400000:
    steps += 1
    b = d[pos]; pos += 1; c, ch = b >> 4, b & 15
    if c == 0: stack.append(pos + 2); pos = d[pos] | d[pos + 1] << 8
    elif c == 1:
        if not ch: pos += 1
    elif c == 2: instr[ch] = d[pos:pos + 26]; pos += 26
    elif c in (3, 7, 0xD): other[c] += 1
    elif c in (4, 5): other[(c, ch, d[pos], d[pos+1])] += 1; pos += 2
    elif c == 6: other[(6, ch, d[pos])] += 1; pos += 1
    elif c == 8: pos += 1
    elif c == 9:
        n, v = d[pos], d[pos + 1]; pos += 2
        deg = n & 31; row, i = divmod(deg, 8)
        semi = [0, 0, 2, 4, 5, 7, 9, 11][i] + (0, 1, -1)[row]
        midi = 12 * ((n >> 5) + 1) + semi
        x = info[ch]; x["notes"] += 1; x["lo"] = min(x["lo"], midi); x["hi"] = max(x["hi"], midi); x["vel"].add(v)
    elif c == 0xA: info[ch]["ctl"].add((d[pos], d[pos + 1])); pos += 2
    elif c == 0xB:
        s = pos
        while d[pos] != 0xF7: pos += 1
        sysex.append(d[s - 1:pos + 1]); pos += 1
    elif c == 0xC: info[ch]["prog"].append(d[pos]); pos += 1
    elif c == 0xE: pos += 3
    else:
        if b == 0xFF:
            if stack: pos = stack.pop()
            else: break
        else: break
names = "C C# D Eb E F F# G Ab A Bb B".split()
nm = lambda m: f"{names[m % 12]}{m // 12 - 1}"
print(Path(sys.argv[1]).name, len(d), "bytes")
for k, v in sorted(instr.items()):
    print(f" instr {k:2d}: opl {v[:11].hex(' ')} | rest {v[11:].hex(' ')}")
for s in sysex[:6]:
    print(" sysex", s[:40].hex(" "), "..." if len(s) > 40 else "", len(s))
print(" sysex blocks", len(sysex))
for ch, x in sorted(info.items()):
    if x["notes"] or x["prog"]:
        ctl = sorted({c for c, _ in x["ctl"]})
        print(f" ch{ch:2d}: {x['notes']:4d} notes {nm(x['lo']) if x['notes'] else '-'}..{nm(x['hi']) if x['notes'] else '-'} "
              f"vel {sorted(x['vel'])[:8]} prog {sorted(set(x['prog']))} ctl# {ctl}")
print(" other", dict(list(other.items())[:12]))
