#!/usr/bin/env python3
"""Rewrite the three PeasantF1 blocks of assets_dev/worlds/mm6/models/actors.yml (PeasantF1 A, PeasantF1 B, Peasantf1 C) for the rebuild;
everything else byte-identical. Temp file + os.replace (assets_dev files are hard links). Run from the repo root: <this> [scale]"""
import os, re, sys, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm6/models/actors.yml')
SCALE = sys.argv[1] if len(sys.argv) > 1 else '103.46'
WALK, RUN = os.environ.get('WALK_STRIDE', '1.24'), os.environ.get('RUN_STRIDE', '1.554')
COMMENT = ('# MM6 female peasant (pfem), rebuilt 2026-11-11 (level_generation/creatures/mm6_pfem_rebuild_claude): the v3 body on MM9\'s PeasantFemale\n'
           '# skeleton and clips, MPFB five-finger arms, 4K head/body paints; palettes 786/787/788. Attack = a restrained MM9 talk gesture.\n')
def block(desc, skin, ref):
    return (f'- descriptor: {desc}\n  model: worlds/mm6/models/mm6_pfem.glb\n  scale: {SCALE}\n' + (f'  scale_reference: {ref}\n' if ref else '') +
            '  yaw_offset: -1.570796327\n  animation:\n    cast: Attack\n    run: Running\n'
            f'    stride_length: {WALK}\n    run_stride_length: {RUN}\n    upper_body_root: FHP Spine1\n'
            '    look:\n      nodes: [FHP Neck, FHP Head]\n      max_yaw_degrees: 60\n      max_pitch_degrees: 35\n'
            '    events:\n      attack_melee: {impact: 0.48}\n      attack_ranged: {impact: 0.48}\n'
            '  clips:\n    standing: Standing\n    walking: Walk2\n    attack_melee: Attack\n    attack_ranged: Attack\n    hit: Hit\n'
            f'    dying: Death\n    dead: Dead\n    fidget: Fidget\n  skin: {skin}\n')
s = A.read_text()
start = s.index('# MM6 female peasant (pfem)')
end = s.index('- descriptor:', s.index('- descriptor: Peasantf1 C') + 10)
while True:                                     # the next entry's own comment lines stay with it
    prev = s.rfind('\n', 0, end - 1) + 1
    if s[prev:end].startswith('#'): end = prev
    else: break
new = COMMENT + block('PeasantF1 A', 'pfem_a', None) + block('PeasantF1 B', 'pfem_b', 'PeasantF1 A') + block('Peasantf1 C', 'pfem_c', 'PeasantF1 A')
out = s[:start] + new + s[end:]
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml'); os.close(fd)
Path(tmp).write_text(out); os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', SCALE, 'chars', len(s), '->', len(out))
