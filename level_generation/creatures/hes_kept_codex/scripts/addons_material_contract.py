"""Preserve the project's packed specular/roughness/metallic map in every Enforcer export."""
import sys
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,write_glb,add_image,compact
for path in (P/'export').glob('hes_kept_m_enforcer*.glb'):
 d,b=read_glb(path)
 for m in d['materials']:
  if not m.get('name','').startswith('KeptV2_plate'):continue
  pbr=m['pbrMetallicRoughness'];old=pbr['metallicRoughnessTexture']['index'];pbr['metallicRoughnessTexture']['index']=add_image(d,b,Image.open(P/'textures/props_v2/plate_metal_rough.png'),'plate_material_mask',d['textures'][old].get('sampler'));pbr['metallicFactor']=0.
 write_glb(path,*compact(d,b));print('PLATE_MATERIAL',path.name)
