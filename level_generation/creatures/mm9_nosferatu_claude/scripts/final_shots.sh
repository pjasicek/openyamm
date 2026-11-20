#!/bin/bash
# every review sheet from the current viewer build. scripts/final_shots.sh
. scripts/env.sh
for t in a b c; do scripts/vs2.sh nos_$t review/shots ${t}_st_q:Standing:0.33:quarter:body ${t}_st_f:Standing:0.33:front:body ${t}_b:Standing:0.33:back:body ${t}_head:Standing:0.33:front:head; done
scripts/vs2.sh nos_b review/shots cmp_at:AttackMelee:0.33:quarter:body cmp_hi:Hit:0.42:quarter:body cmp_de:Death:1.0:quarter:body cmp_ra:AttackRanged:0.7:quarter:body
python3 - <<'P'
from PIL import Image, ImageDraw
s = 420; W = Image.new('RGB', (s * 6, s * 3), (40, 40, 40))
def sq(p):
    m = Image.open(p).convert('RGB'); w, h = m.size; q = min(w, h)
    return m.crop(((w - q) // 2, (h - q) // 2, (w + q) // 2, (h + q) // 2)).resize((s, s), Image.LANCZOS)
for r, t in enumerate('abc'):
    n = r + 1
    row = [(f'review/mm9_cmp/st{n}_q34.png', 'MM9 3/4'), (f'review/shots/{t}_st_q.png', 'ours'), (f'review/mm9_cmp/st{n}_front.png', 'MM9 front'), (f'review/shots/{t}_st_f.png', 'ours'), (f'review/mm9_cmp/st{n}_back.png', 'MM9 back'), (f'review/shots/{t}_b.png', 'ours')]
    for i, (p, lab) in enumerate(row):
        im = sq(p); ImageDraw.Draw(im).text((4, 4), f'{t} {lab}', fill=(255, 255, 0)); W.paste(im, (i * s, r * s))
W.save('review/mm9_vs_ours.png')
W = Image.new('RGB', (s * 4, s * 2), (40, 40, 40))
for i, (c, sh) in enumerate((('Hattack1', 'cmp_at'), ('wince1', 'cmp_hi'), ('die1', 'cmp_de'), ('RAttack1', 'cmp_ra'))):
    W.paste(sq(f'review/mm9_cmp/{c}_q34.png'), (i * s, 0)); W.paste(sq(f'review/shots/{sh}.png'), (i * s, s))
W.save('review/mm9_vs_ours_clips.png')
L = [sq(f'review/shots/{t}_head.png') for t in 'abc']
W = Image.new('RGB', (s * 3, s))
for i, m in enumerate(L): W.paste(m, (i * s, 0))
W.save('review/sheet_heads.png')
P
for t in a b c; do scripts/strips.sh $t; done
for t in a b c; do scripts/closeups.sh nos_$t ${t}_; python3 scripts/sheet.py review/sheet_closeups_$t.png 330 6 ${t}_cr0 ${t}_cr1 ${t}_cr2 ${t}_cr3 ${t}_cr4 ${t}_cr5 ${t}_cr6 ${t}_cr7 ${t}_ra0 ${t}_ra1 ${t}_ra2 ${t}_fi0 ${t}_fi1 ${t}_fi2 ${t}_fi3 ${t}_de0 ${t}_de1 ${t}_de2 ${t}_de3 ${t}_de4 ${t}_de5 ${t}_de6 ${t}_de7 ${t}_dd0 ${t}_dd1 ${t}_dd2 ${t}_dd3 ${t}_dd4 ${t}_dd5 ${t}_dd6 ${t}_dd7 ${t}_st0 ${t}_st1 ${t}_st2 ${t}_st3 ${t}_st4 ${t}_st5; done
echo FINALSHOTS
