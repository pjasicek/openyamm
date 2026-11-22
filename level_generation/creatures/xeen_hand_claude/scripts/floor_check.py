#!/usr/bin/env python3
"""Floor audit (claude_shared/floor/floor_audit.audit) of export/xeen_hand.glb with the binding block in
integration/actors.yml (the binding is not merged into the world's actors.yml)."""
import sys, json
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared' / 'floor'))
import floor_audit as F
actors = yaml.safe_load((ROOT / 'integration/actors.yml').read_text())['actors']
for a in actors:
    a['model'] = str(ROOT / 'export/xeen_hand.glb')
print(json.dumps(F.audit('xeen', None, 2.5, 0.01, actors), indent=1))
