#!/usr/bin/env python3
"""Rewrite the three BThief blocks of assets_dev/worlds/mm6/models/actors.yml (BThief A, B, C) for the rebuild; everything else byte-identical.
Temp file + os.replace (assets_dev files are hard links). Run from the repo root: <this> [scale]   (strides: env WALK_STRIDE, RUN_STRIDE, SPRINT_STRIDE)"""
import os, sys, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm6/models/actors.yml')
SCALE = sys.argv[1] if len(sys.argv) > 1 else '93.26'
WALK, RUN, SPRINT = os.environ['WALK_STRIDE'], os.environ['RUN_STRIDE'], os.environ['SPRINT_STRIDE']
COMMENT = ('# MM6 thief / burglar / rogue (thf), rebuilt 2026-11-11 (level_generation/creatures/mm6_thf_rebuild_claude): the gated HD masters\' Smart\n'
           '# Topology on MM9\'s HIGHWAYMAN skeleton and its FIGHTERBASE clips, MPFB five-finger hands, the cloak on 14 keyed chains, the approved\n'
           '# daggers on MM9\'s Ybasesword / Ybasedagger (shown only in the attacks). One shared texture set + head set; the cloak, hood and\n'
           '# undershirt follow palettes 825/826/827 (region ramps). Attack: Hattack3 x1.2 (contact 0.375 s); thrown dagger: Rattack1 x1.2\n'
           '# (release 0.417 s from the left fist). Scale: native stand frame 171.5 units against the 1.839 m Standing height.\n')


def block(desc, skin, ref):
    return (f'- descriptor: {desc}\n  model: worlds/mm6/models/mm6_thf.glb\n  scale: {SCALE}\n' + (f'  scale_reference: {ref}\n' if ref else '') +
            '  yaw_offset: -1.570796327\n  animation:\n    cast: Attack\n    run: Jog\n'
            f'    stride_length: {WALK}\n    run_stride_length: {RUN}\n    sprint: Running\n    sprint_stride_length: {SPRINT}\n'
            '    upper_body_root: Bip01 Spine1\n'
            '    look:\n      nodes: [Bip01 Neck, Bip01 Head]\n      max_yaw_degrees: 60\n      max_pitch_degrees: 35\n'
            '    sockets:\n      dagger: Ybasedagger\n'
            '    events:\n      attack_melee: {impact: 0.375}\n      attack_ranged: {impact: 0.417, release: dagger}\n'
            '  clips:\n    standing: Standing\n    walking: Walk2\n    attack_melee: Attack\n    attack_ranged: AttackRanged\n    hit: Hit\n'
            f'    dying: Death\n    dead: Dead\n    fidget: Fidget\n  script_clips:\n    attack2: Attack2\n  skin: {skin}\n')


s = A.read_text()
start = s.index('# MM6 thief / burglar / rogue (thf)')
end = s.index('- descriptor:', s.index('- descriptor: BThief C') + 10)
while True:                                     # the next entry's own comment lines stay with it
    prev = s.rfind('\n', 0, end - 1) + 1
    if s[prev:end].startswith('#'): end = prev
    else: break
new = COMMENT + block('BThief A', 'thf_a', None) + block('BThief B', 'thf_b', 'BThief A') + block('BThief C', 'thf_c', 'BThief A')
out = s[:start] + new + s[end:]
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml'); os.close(fd)
Path(tmp).write_text(out); os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', SCALE, 'chars', len(s), '->', len(out))
