"""Embed the staged manifest for an offline animation and palette viewer."""
import json
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--redo', action='store_true')
args = parser.parse_args()
template = ROOT/'viewer.html'
if args.redo:
    ROOT = ROOT/'redo_2x'
manifest=json.loads((ROOT/'manifest.json').read_text())
s=template.read_text();assert s.count('/* MANIFEST */')==1
(ROOT/'review.html').write_text(s.replace('/* MANIFEST */',json.dumps(manifest,separators=(',',':'))))
print(ROOT/'review.html')
