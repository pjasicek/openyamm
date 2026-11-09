"""Preserve LOD0/rig/clips, add three colour and shadow LODs, then shared palette variants."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

PROJECT=Path(__file__).resolve().parents[1];REPO=PROJECT.parents[2];OUT=PROJECT/'export'
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import read_glb,write_glb,generate
doc,binary=read_glb(OUT/'wolf_lod0_raw.glb');binary=bytearray(binary)
for material in doc['materials']:
    assert material['name']=='Wolf'
    pbr=material['pbrMetallicRoughness'];pbr['metallicFactor']=0
    material.setdefault('extras',{})['openyamm_specular']=0
    index=doc['textures'][pbr['metallicRoughnessTexture']['index']]['source']
    data=(PROJECT/'textures/wolf_metal_rough_1k.png').read_bytes()
    binary.extend(b'\0'*(-len(binary)%4));view=len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)})
    binary.extend(data);doc['images'][index]={'name':'Wolf_MR_AO','bufferView':view,'mimeType':'image/png'}
write_glb(OUT/'wolf_maps.glb',doc,binary)
subprocess.run(['/usr/bin/python3',str(REPO/'tools/prepare_actor_glb.py'),str(OUT/'wolf_maps.glb'),
                str(OUT/'wolf_lod0.glb')],check=True)
generate(OUT/'wolf_lod0.glb',OUT/'wolf_lods.glb','Wolf',ratios=(.5,.25,.125),max_influences=4)
subprocess.run(['/usr/bin/python3',str(PROJECT/'scripts/finish_runtime.py')],check=True)
