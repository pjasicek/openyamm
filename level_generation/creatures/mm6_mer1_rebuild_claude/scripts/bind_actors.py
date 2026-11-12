#!/usr/bin/env python3
"""Rewrite the three Merchant blocks of assets_dev/worlds/mm6/models/actors.yml (Merchant A, B, C) for the rebuild; everything else byte-identical.
Temp file + os.replace (assets_dev files are hard links). Run from the repo root: <this> <scale> <impact s>  (strides: env WALK_STRIDE, RUN_STRIDE)"""
import os, sys, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm6/models/actors.yml')
SCALE, IMPACT = sys.argv[1], sys.argv[2]
WALK, RUN = os.environ['WALK_STRIDE'], os.environ['RUN_STRIDE']
COMMENT = ('# MM6 Peasant Merchant (mer1, monster IDs 577-579), rebuilt 2026-11-11 (level_generation/creatures/mm6_mer1_rebuild_claude): the gated\n'
           '# round-2 HD masters\' Smart Topology on MM9\'s HIGHWAYMAN/FIGHTERBASE skeleton, body clips from MM9 NOBLEMAN (same Bip01 names),\n'
           '# FIGHTERBASE Hattack2 as the club blow, MPFB five-finger hands, the tunic skirt on 16 keyed chains. As the native merchant the club\n'
           '# hangs at his right hip (joint Club, riding the robe) and is drawn into the fist in the attack. One shared texture set + head set;\n'
           '# the tunic follows palettes 252/253/770 (region ramps). Scale: native stand 177.1 units against the 1.744 m Standing height.\n')


def block(desc, skin, ref):
    return (f'- descriptor: {desc}\n  model: worlds/mm6/models/mm6_mer1.glb\n  scale: {SCALE}\n' + (f'  scale_reference: {ref}\n' if ref else '') +
            '  yaw_offset: -1.570796327\n  animation:\n    cast: Attack\n    run: Jog\n'
            f'    stride_length: {WALK}\n    run_stride_length: {RUN}\n'
            '    upper_body_root: Bip01 Spine1\n'
            '    look:\n      nodes: [Bip01 Neck, Bip01 Head]\n      max_yaw_degrees: 25\n      max_pitch_degrees: 12\n'
            f'    events:\n      attack_melee: {{impact: {IMPACT}}}\n      attack_ranged: {{impact: {IMPACT}}}\n      cast: {{impact: {IMPACT}}}\n'
            '  clips:\n    standing: Standing\n    walking: Walk2\n    attack_melee: Attack\n    attack_ranged: Attack\n    hit: Hit\n'
            f'    dying: Death\n    dead: Dead\n    fidget: Fidget\n  skin: {skin}\n'
            '  attachments:\n  - model: worlds/mm6/models/mm6_mer1_club.glb\n    node: Club\n')


s = A.read_text()
start = s.index('# MM6 Peasant Merchant (mer1')
end = s.index('- descriptor:', s.index('- descriptor: Merchant C') + 10)
while True:                                     # the next entry's own comment lines stay with it
    prev = s.rfind('\n', 0, end - 1) + 1
    if s[prev:end].startswith('#'): end = prev
    else: break
new = COMMENT + block('Merchant A', 'mer1_a', None) + block('Merchant B', 'mer1_b', 'Merchant A') + block('Merchant C', 'mer1_c', 'Merchant A')
out = s[:start] + new + s[end:]
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml'); os.close(fd)
Path(tmp).write_text(out); os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', SCALE, 'chars', len(s), '->', len(out))
