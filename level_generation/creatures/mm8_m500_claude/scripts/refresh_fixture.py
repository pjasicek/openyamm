from pathlib import Path
import json,struct,os,hashlib,yaml
p=Path(__file__).resolve().parents[1];root=p.parents[2]
fixture=Path(json.loads((p/'review/ingame/indoor_fixture.json').read_text())['assets_root']);relative=Path('worlds/mm8/models/mm8_m500.glb')
raw=(root/'assets_dev'/relative).read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);paths=[relative]+[relative.parent/i['uri'] for i in doc['images']];receipts=[]
for rel in paths:
 dst=fixture/rel;dst.unlink(missing_ok=True);os.link(root/'assets_dev'/rel,dst);sha=hashlib.sha256(dst.read_bytes()).hexdigest();assert sha==hashlib.sha256((root/'assets_dev'/rel).read_bytes()).hexdigest();receipts.append({'path':str(rel),'sha256':sha})
# Keep unrelated in-progress MM8 bindings from entering this private, frozen asset fixture.
rel=Path('worlds/mm8/models/actors.yml');source=yaml.safe_load((root/'assets_dev'/rel).read_text());rows=[r for r in source['actors'] if r['descriptor'] in ['Water Elemental A','Water Elemental B','Water Elemental C']];assert len(rows)==3
(fixture/rel).unlink();(fixture/rel).write_text(yaml.safe_dump({'actors':rows},sort_keys=False))
receipts.append({'path':str(rel),'sha256':hashlib.sha256((fixture/rel).read_bytes()).hexdigest(),'scope':'Only the three Water Elemental rows, identical to the source bindings.'})
(p/'review/ingame/fixture_model_hashes.json').write_text(json.dumps(receipts,indent=2)+'\n');print('REFRESHED',fixture)
