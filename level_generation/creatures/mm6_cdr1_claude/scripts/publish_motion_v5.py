"""Refresh the existing viewer for the scoped v6 Attack/Cast correction."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
checks=json.loads((P/'review/motion_v6/checks.json').read_text())
manifest=json.loads((V/'manifest.json').read_text());manifest['revision']='v6-wing-windup';manifest['default_clip']='Attack'
for model in manifest['models']:
 name=model['url'].split('?')[0];sha=hashlib.sha256((V/name).read_bytes()).hexdigest()
 model.update(url=name+'?v='+sha[:12],sha256=sha,revision=manifest['revision'])
for name in ('Attack','Cast'):
 clip=manifest['clips'][name]
 clip['provenance']='v6: broader wing fold shared between middle/distal joints; head turns into the windup during the opening 0.15s. Native-informed timing, impact retained at 0.75s.'
 assert clip['duration']==checks['clips'][name]['duration']==1.0
 assert clip['impact']==.75
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Updated viewer revision; gameplay bindings and clip durations retained')
