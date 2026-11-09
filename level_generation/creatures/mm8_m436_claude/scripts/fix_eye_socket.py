"""Name left/right eyes relative to the fitted head centre, not the world origin."""
from pathlib import Path
import bpy,json,struct,hashlib
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/m436_textured_master.blend'));rig=bpy.data.objects['Rig'];eyes=[b for b in rig.data.bones if b.name.startswith('Socket_Eye')];assert len(eyes)==2
left=max(eyes,key=lambda b:b.head_local.x);assert left.name=='Socket_Eye_Right.001';left.name='Socket_Eye_Left';bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/m436_textured_master.blend'))
for path in [*p.glob('export/mm8_m436*.glb'),*p.glob('review/viewer/mm8_m436_?.glb')]:
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:];names=[node.get('name') for node in doc['nodes']];assert names.count('Socket_Eye_Right.001')==1 and 'Socket_Eye_Left' not in names
 doc['nodes'][names.index('Socket_Eye_Right.001')]['name']='Socket_Eye_Left';enc=json.dumps(doc,separators=(',',':')).encode();enc+=b' '*(-len(enc)%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(enc)+len(binary))+struct.pack('<II',len(enc),0x4e4f534a)+enc+struct.pack('<II',len(binary),0x004e4942)+binary)
v=p/'review/viewer';f=v/'manifest.json';d=json.loads(f.read_text())
for model in d['models']:
 name=model['url'].split('?')[0];h=hashlib.sha256((v/name).read_bytes()).hexdigest();model.update(url=name+'?sha256='+h,sha256=h)
f.write_text(json.dumps(d,indent=2)+'\n')
