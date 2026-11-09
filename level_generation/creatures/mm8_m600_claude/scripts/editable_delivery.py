from pathlib import Path
import bpy,json,struct
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/nightmare_final.blend'))
raw=(P/'export/mm8_m600_prepared.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);blob=raw[28+n:]
mat=next(m for m in d['materials'] if m['name']=='Nightmare')
image=d['images'][d['textures'][mat['normalTexture']['index']]['source']];v=d['bufferViews'][image['bufferView']]
normal=P/'work/normal_gltf.png';normal.write_bytes(blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
for node in bpy.data.materials['Nightmare'].node_tree.nodes:
 if node.type!='TEX_IMAGE':continue
 if node.image.name.startswith('body_basecolor'):
  node.image=bpy.data.images.load(str(P/'work/tier_nightmare_a_Nightmare.png'));node.image.colorspace_settings.name='sRGB'
 elif node.image.name.startswith('body_normal'):
  node.image=bpy.data.images.load(str(normal));node.image.colorspace_settings.name='Non-Color'
for image in bpy.data.images:
 if image.source=='FILE' and image.filepath:image.pack()
assert len(bpy.data.objects['NightmareRig'].data.bones)==58
assert len(bpy.data.actions)==7
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/nightmare.blend'))
print('Packed editable master: final A appearance, glTF normals, no baked attack FX, seven actions')
