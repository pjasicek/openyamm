#!/usr/bin/env python3
"""Floor audit (claude_shared/floor/floor_audit.audit) of integration/actors.yml on a GLB of this project
(default export/xeen_saber.glb) before the parent merges the binding. Usage: floor_check.py [glb]"""
import sys, json, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared' / 'floor'))
import floor_audit as F
glb = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'export/xeen_saber.glb'
actors = yaml.safe_load((ROOT / 'integration/actors.yml').read_text())['actors']
for a in actors:
    a['model'] = str(glb)
for r in F.audit('xeen', None, 2.5, 0.01, actors):
    print('FLOOR', json.dumps(r))
