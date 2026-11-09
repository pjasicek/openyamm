import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));import build_actor_lods as R
D=P/'textures/gltf';D.mkdir(exist_ok=True);doc,binary=R.read_glb(P/'export/mm8_m576_prepared.glb');maps={}
for mat in doc['materials']:
 i=doc['textures'][mat['normalTexture']['index']]['source'];im=doc['images'][i];v=doc['bufferViews'][im['bufferView']];name=im['name'];path=D/(name+'.png');path.write_bytes(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);maps[name]=path
bpy.ops.wm.open_mainfile(filepath=str(P/'work/triton_final.blend'))
for image in bpy.data.images:
 stem=Path(image.filepath).stem
 if stem in maps:
  image.unpack(method='REMOVE') if image.packed_file else None
  image.filepath=str(maps[stem]);image.reload()
 if stem in ('body_orm','head_orm'):
  image.unpack(method='REMOVE') if image.packed_file else None
  image.filepath=str(P/'textures'/(stem+'.png'));image.reload()
 for part,material in [('body','Triton_A'),('head','TritonHead_A')]:
  if stem==part+'_basecolor':
   image.unpack(method='REMOVE') if image.packed_file else None
   image.filepath=str(P/f'work/tier_triton_a_{material}.png');image.reload()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/triton.blend'))
