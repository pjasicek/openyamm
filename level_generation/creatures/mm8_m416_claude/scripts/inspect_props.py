from pathlib import Path
import bpy,bmesh,sys,json,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
for item,size in [('crossbow',.72),('quiver',.55)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/f'meshy/{item}_v1/model_urls_glb.glb'))
 obs=[o for o in bpy.data.objects if o.type=='MESH'];lo,hi=common.world_bounds(obs);k=size/max(hi-lo);centre=(hi+lo)/2
 for o in obs:
  for v in o.data.vertices:v.co=(o.matrix_world@v.co-centre)*k
  o.matrix_world.identity()
 for o in bpy.data.objects:o.select_set(o in obs)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000001);bm.to_mesh(o.data);bm.free()
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
 obs=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.polygons),reverse=True);report=[]
 for i,o in enumerate(obs):
  o.name=f'{item}_{i:02}';co=np.array([v.co[:] for v in o.data.vertices]);report.append({'name':o.name,'vertices':len(co),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'lo':co.min(0).tolist(),'hi':co.max(0).tolist(),'mean':co.mean(0).tolist()})
 (P/f'work/{item}_parts.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{item}_raw.blend'));common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/f'review/{item}_raw'),0,size*1.35,views=('front','left','back','three_quarter'),resolution=(600,600));print('PROP',item,json.dumps(report))
