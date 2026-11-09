"""Inspect original Smart Topology geometry; normalize to 2 m without changing proportions."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm8_m584_claude/scripts'))
import common
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_v1/model_urls_glb.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=meshes[0]
if len(meshes)>1:bpy.ops.object.join()
obj=bpy.context.object
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
c=np.array([tuple(v.co) for v in obj.data.vertices]);s=2/(c[:,2].max()-c[:,2].min())
obj.scale=(s,)*3;obj.location=(-(c[:,0].max()+c[:,0].min())*.5*s,-(c[:,1].max()+c[:,1].min())*.5*s,-c[:,2].min()*s)
bpy.ops.object.transform_apply(location=True,scale=True)
obj.data.materials.clear()
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
report=[]
colors=[(.65,.27,.23,1),(.23,.58,.3,1),(.25,.36,.75,1),(.7,.58,.2,1),(.65,.3,.65,1),(.2,.6,.6,1)]
for i,o in enumerate(sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:-len(o.data.vertices))):
 c=np.array([tuple(v.co) for v in o.data.vertices]);bm=bmesh.new();bm.from_mesh(o.data)
 r={'name':f'Part{i:02d}','verts':len(c),'tris':sum(len(f.vertices)-2 for f in o.data.polygons),'min':c.min(0).tolist(),'max':c.max(0).tolist(),'mean':c.mean(0).tolist(),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
 bm.free();o.name=r['name'];report.append(r)
 mat=bpy.data.materials.new(o.name);mat.diffuse_color=colors[i%len(colors)];o.data.materials.append(mat)
 for f in o.data.polygons:f.use_smooth=True
(P/'work/body_parts.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/body_parts.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/body_parts'),1,2.8,views=('front','left','back','three_quarter'),resolution=(800,800))
