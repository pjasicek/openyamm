"""Expose each sculptural LOD as the scene mesh for review at its actual switch size."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(R/'tools'))
from link_static_model_lods import read_glb,write_glb
out=P/'work/lod_review';out.mkdir(exist_ok=True)
for name,d in json.loads((P/'designs.json').read_text()).items():
    if d['route']!='codex':continue
    icon=d['icons'][0];file=P/'work/exports'/f'w02_{icon}_export.glb'
    if not file.exists():continue
    doc,binary=read_glb(file);node=next(n for n in doc['nodes'] if 'mesh' in n)
    levels=doc['meshes'][node['mesh']]['extras']['openyamm_lods'];assert len(levels)==2
    for index,mesh in enumerate(levels,1):
        node['mesh']=mesh;write_glb(out/f'{icon}_lod{index}.glb',doc,binary[:])
