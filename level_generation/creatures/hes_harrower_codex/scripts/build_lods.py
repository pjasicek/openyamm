"""Standard initial LODs; attachments are split before the far-LOD repair pass."""
from pathlib import Path
import sys,json,bpy,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
import build_actor_lods as lod
from build_actor_lods import read_glb,write_glb
for kind in ('family','vreth'):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 source=P/'work'/('assembly_'+kind+'_variants.glb');out=P/'work'/('assembly_'+kind+'_lods.glb')
 # Original hand and head contact geometry survives the first LOD.
 bpy.ops.import_scene.gltf(filepath=str(source));ob=bpy.data.objects['HHW'];rig=next(m.object for m in ob.modifiers if m.type=='ARMATURE')
 protected=[tuple(ob.matrix_world@v.co) for v in ob.data.vertices if (ob.matrix_world@v.co).z>1.52]
 bpy.ops.wm.read_factory_settings(use_empty=True)
 lod.generate(source,out,'HHW',ratios=(.5,.25,.125),max_influences=4,protected_points=protected)
 # The shared LOD helper preserves materials but requires variant mappings copied onto generated primitives.
 j,b=read_glb(out);base=next(m for m in j['meshes'] if m.get('extras',{}).get('openyamm_lods'))
 maps={p['material']:p.get('extensions',{}) for p in base['primitives']}
 for m in j['meshes']:
  for p in m['primitives']:
   if p['material'] in maps:p['extensions']=maps[p['material']]
 write_glb(out,j,b)
