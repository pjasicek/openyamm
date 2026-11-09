#!/usr/bin/env python3
"""Review viewer on a given runtime GLB (texture-quality pass, 2026-10-31): the three tiers share palette 616 and a
zero-coverage mask, so each tier is a copy (as viewer_tiers.py). Usage: viewer_texpass.py <glb> <revision>"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
source, revision = Path(sys.argv[1]), sys.argv[2]
digest = hashlib.sha256(source.read_bytes()).hexdigest()
path = P / 'review/viewer/manifest.json'
manifest = json.loads(path.read_text())
for model in manifest['models']:
    name = 'mm8_' + model['id'] + '.glb'
    shutil.copyfile(source, P / 'review/viewer' / name)
    model.update(sha256=digest, url=name + '?v=' + digest[:12], revision=revision)
manifest.update(revision=revision, model_sha256=digest)
path.write_text(json.dumps(manifest, indent=2) + '\n')
print('VIEWER', revision, digest)
