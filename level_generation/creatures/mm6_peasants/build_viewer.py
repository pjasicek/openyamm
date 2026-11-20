"""Embed one goal family's manifest in the local, offline native/enhanced viewer."""
import argparse
import json
from prepare_family import load, HERE

parser = argparse.ArgumentParser()
parser.add_argument('family')
root, config, _ = load(parser.parse_args().family)
manifest = json.loads((root / 'manifest.json').read_text())
template = (HERE / 'viewer.html').read_text()
assert template.count('/* MANIFEST */') == 1
output = template.replace('__TITLE__', config['title']).replace(
    '/* MANIFEST */', json.dumps(manifest, separators=(',', ':')))
(root / 'review.html').write_text(output)
print(root / 'review.html')
