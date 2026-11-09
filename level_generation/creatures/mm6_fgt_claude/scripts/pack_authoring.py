from pathlib import Path
import bpy,json,struct
p=Path(__file__).resolve().parents[1]
raw=(p/'export/mm6_fgt_runtime_lod0.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);binary=raw[28+n:]
for m in d['materials']:
 if 'normalTexture' in m:
  im=d['images'][d['textures'][m['normalTexture']['index']]['source']];assert im['mimeType']=='image/png'
  view=d['bufferViews'][im['bufferView']];offset=view.get('byteOffset',0)
  name={'Thug_A':'fgt','ThugHead_A':'fgt_head','Mace_A':'fgt_mace'}[m['name']]
  (p/'textures'/(name+'_normal_gltf_1k.png')).write_bytes(binary[offset:offset+view['byteLength']])
bpy.ops.wm.open_mainfile(filepath=str(p/'work/thug_final.blend'))
for mat in bpy.data.materials:
 if mat.name not in ('Thug_A','ThugHead_A','Mace_A'):continue
 for node in mat.node_tree.nodes:
  if node.type!='TEX_IMAGE' or not node.image:continue
  old=node.image.name
  if 'basecolor' in old and mat.name!='Mace_A':node.image=bpy.data.images.load(str(p/'work'/f'tier_fgt_a_{mat.name}.png'));node.image.colorspace_settings.name='sRGB'
  elif 'normal' in old:
   file={'Thug_A':'fgt_normal_gltf_1k.png','ThugHead_A':'fgt_head_normal_gltf_1k.png','Mace_A':'fgt_mace_normal_gltf_1k.png'}[mat.name]
   node.image=bpy.data.images.load(str(p/'textures'/file));node.image.colorspace_settings.name='Non-Color'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'export/mm6_fgt.blend'))
print('PACKED tier A authoring',p/'export/mm6_fgt.blend')
