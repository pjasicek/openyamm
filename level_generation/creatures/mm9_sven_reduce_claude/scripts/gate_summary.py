#!/usr/bin/env python3
"""One-line-per-gate summary of review/gates_<tag>/ (installed vs candidates). Usage: gate_summary.py before <tag> ..."""
import json, re, sys
from pathlib import Path
for t in sys.argv[1:]:
    g = Path(f'review/gates_{t}'); out = []
    try:
        ah = json.loads((g / 'arm_hand.json').read_text())
    except Exception:
        ah = None
    txt = lambda n: (g / f'{n}.txt').read_text() if (g / f'{n}.txt').exists() else ''
    a = txt('arm_hand')
    hands = re.findall(r'(\w+)\s+L: hand ([\d.]+)cm@\d+ \((\d+)f>1cm\) forearm ([\d.]+)cm.*?\| R: hand ([\d.]+)cm@\d+ \((\d+)f>1cm\) forearm ([\d.]+)cm', a)
    out.append('arm/hand ' + '; '.join(f'{c} L{h1}/{f1}f fa{fa1} R{h2}/{f2}f fa{fa2}' for c, h1, f1, fa1, h2, f2, fa2 in hands
                                         if float(h1) > 0 or float(h2) > 0 or float(fa1) > 0 or float(fa2) > 0))
    j = re.findall(r'JITTER fails (\d+)', txt('jitter')); out.append(f'jitter fails {j}')
    sp = re.findall(r'(\w+)\s+L: poke ([\d.]+)mm@\d+ \((\d+)f.*?R: poke ([\d.]+)mm@\d+ \((\d+)f', txt('sleeve_poke'))
    out.append('sleeve poke ' + ('; '.join(f'{c} L{a_}/{b}f R{c_}/{d}f' for c, a_, b, c_, d in sp if float(a_) or float(c_)) or 'all 0'))
    col = re.findall(r'(\w+)\s+face-frames\s+(\d+)', txt('collapse')); out.append('collapse ' + ' '.join(f'{c}:{n}' for c, n in col))
    for n in ('detached', 'flat', 'bone_length', 'winding', 'same_clips', 'texture_quality'):
        s = txt(n).strip().splitlines()
        out.append(f'{n}: ' + ' | '.join(x.strip()[:170] for x in s if re.search(r'detached|flat|stretch|WINDING|SAME|DIFF|atlas', x))[:600])
    print(f'== {t}'); print('\n'.join(out))
