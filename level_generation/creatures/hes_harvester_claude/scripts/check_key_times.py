#!/usr/bin/env python3
"""Key-time gate: every animation sampler input of every given GLB must be finite and strictly increasing, as stored
(float32). The engine rejects the whole model otherwise ("animation <clip> keyframe times are not finite and strictly
increasing"); the first floor fix of 2026-10-22 merged a 1/120 s grid time with an existing key that differed only
below float32 precision, so B_Pelvis translation had two Death keys at 2.1 s.
Usage: check_key_times.py <glb> [...]  (exit 1 on any failure)"""
import json, struct, sys
from pathlib import Path
import numpy as np


def inputs(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
    for a in doc.get('animations', []):
        for k, s in enumerate(a['samplers']):
            acc = doc['accessors'][s['input']]; view = doc['bufferViews'][acc['bufferView']]
            start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
            t = np.frombuffer(binary, np.float32, acc['count'], start)
            targets = [doc['nodes'][c['target']['node']].get('name') + '.' + c['target']['path']
                       for c in a['channels'] if c['sampler'] == k]
            yield a.get('name'), targets, t


bad = 0
for path in sys.argv[1:]:
    channels = failures = 0
    for clip, targets, t in inputs(path):
        channels += 1
        if not np.isfinite(t).all() or (len(t) > 1 and not (np.diff(t) > 0).all()):
            failures += 1
            i = int(np.argmin(np.diff(t))) if len(t) > 1 else 0
            print(f'KEYTIMES FAIL {Path(path).name} {clip} {targets} keys {i}/{i + 1}: {t[i]!r} {t[min(i + 1, len(t) - 1)]!r}')
    print(f'KEYTIMES {"PASS" if not failures else "FAIL"} {path}: {channels} samplers, {failures} bad')
    bad += failures
sys.exit(1 if bad else 0)
