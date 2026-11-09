"""Make an animation-inventory-only probe for the unmodified shared runner."""
import json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb
source=P/'export/mm6_natm.glb';d,b=read_glb(source);d['animations']=[a for a in d['animations']if a['name']in ['Attack']];write_glb(P/'review/round5_probe.glb',d,b)
c=json.loads((P/'gates.json').read_text())
for prop in c['props']:prop['file']='../'+prop['file']
(P/'review/round5_probe.gates.json').write_text(json.dumps(c,indent=2))
(P/'review/round5_probe_provenance.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'changes':'Only animation inventory narrowed to Attack; geometry, skeleton, materials and animation data unchanged.'},indent=2))
