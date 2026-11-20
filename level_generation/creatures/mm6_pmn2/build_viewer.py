"""Embed the staged manifest for an offline animation and palette viewer."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
s=(ROOT/'viewer.html').read_text();assert s.count('/* MANIFEST */')==1
(ROOT/'review.html').write_text(s.replace('/* MANIFEST */',json.dumps(manifest,separators=(',',':'))))
print(ROOT/'review.html')
