"""Which bones weight MM9 PeasantDM3's head/hair vertices, by height band (MM9 units -> m)."""
import sys
from pathlib import Path
from collections import Counter
sys.path.insert(0, 'tools/mm9_import_discovery')
import convert_abc_model as abc
for stem in sys.argv[1:]:
    m = abc.read_abc(Path(f'mm9/extracted/MODELS/MODELS/{stem}.abc'))
    names = [n.name for n in m.nodes]
    print(stem, [p.name for p in m.pieces])
    bands = {}
    for piece in m.pieces:
        for v in piece.lods[0].vertices:
            z = v.position[1] * 0.0256 if True else 0
            key = None
            ws = sorted(v.weights, key=lambda w: -w.bias)
            if any('Ponytail' in names[w.node_index] or 'Head' in names[w.node_index] or 'Bone03' in names[w.node_index] for w in ws):
                b = round(z * 20) / 20
                bands.setdefault(b, Counter())['+'.join(f'{names[w.node_index].replace("Bip01 ","")}:{w.bias:.2f}' for w in ws[:2])] += 1
    for b in sorted(bands):
        print(f'  y {b:+.2f}', bands[b].most_common(4))
