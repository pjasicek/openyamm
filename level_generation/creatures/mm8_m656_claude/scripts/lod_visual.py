import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
sys.path.insert(0,str(P.parents[2]/'tools'));from build_actor_lods import read_glb,write_glb
for level in range(4):
 d,b=read_glb(P/'export/mm8_m656_lods.glb');node=next(n for n in d['nodes'] if n.get('name')=='Mercenary');base=d['meshes'][node['mesh']]
 if level:node['mesh']=base['extras']['openyamm_lods'][level-1]
 if level>1:
  sword=next(q for q in d['meshes'][base['extras']['openyamm_lods'][0]]['primitives'] if d['materials'][q['material']]['name']=='MercenarySword_A')
  d['meshes'][node['mesh']]['primitives']=[sword if d['materials'][q['material']]['name']=='MercenarySword_A' else q for q in d['meshes'][node['mesh']]['primitives']]
 temp=P/'work'/f'lod_review_{level}.glb';write_glb(temp,d,b)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(temp));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Mercenary'];sc=bpy.context.scene
 common.workbench_clay(sc,True);sc.display.shading.show_specular_highlight=False
 for name,t in [('Standing',0),('Running',.33),('Attack',1.017),('Dead',.5)]:
  rig.animation_data.action=None
  for bone in rig.pose.bones:bone.matrix_basis.identity()
  a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*30;sc.frame_set(int(f),subframe=f%1)
  lo,hi=common.world_bounds([body]);center=(lo+hi)/2
  common.render_views(str(P/'review'/f'lod{level}_{name}'),center.z,max(2.2,(hi-lo).length*.9),views=('three_quarter',),resolution=(500,700),target=(center.x,center.y))
