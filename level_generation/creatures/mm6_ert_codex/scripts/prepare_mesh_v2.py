"""Import the immutable Meshy return, normalize to 2.4 m standing height, inspect topology."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/geometry_v2/model_urls_glb.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert meshes,'Meshy GLB has no mesh'
for o in bpy.data.objects: o.select_set(o in meshes)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join(); mesh=bpy.context.object; mesh.name='Body'; mesh.data.name='Body'
mesh.parent=None; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bm=bmesh.new(); bm.from_mesh(mesh.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6); bm.to_mesh(mesh.data); bm.free()
co=np.array([v.co[:] for v in mesh.data.vertices]); k=2.4/(co[:,2].max()-co[:,2].min())
co*=k; co[:,0]-=(co[:,0].max()+co[:,0].min())/2; co[:,1]-=(co[:,1].max()+co[:,1].min())/2; co[:,2]-=co[:,2].min()
for v,c in zip(mesh.data.vertices,co): v.co=c
for poly in mesh.data.polygons: poly.use_smooth=True
adj=[[] for _ in co]
for e in mesh.data.edges:
    a,b=e.vertices; adj[a].append(b); adj[b].append(a)
seen=set(); parts=[]
for i in range(len(co)):
    if i in seen: continue
    stack=[i]; seen.add(i); ids=[]
    while stack:
        a=stack.pop(); ids.append(a)
        for b in adj[a]:
            if b not in seen: seen.add(b); stack.append(b)
    parts.append(ids)
parts.sort(key=len,reverse=True)
report={'vertices':len(co),'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'bounds':[co.min(0).tolist(),co.max(0).tolist()],'components':[{'vertices':len(ids),'bounds':[co[ids].min(0).tolist(),co[ids].max(0).tolist()],'indices':ids} for ids in parts]}
assert report['triangles']>5000 and np.isfinite(co).all()
(P/'work/geometry_inspection.json').write_text(json.dumps(report))
np.save(P/'work/rest_vertices.npy',co)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_v2.blend'))
scene=bpy.context.scene; scene.world=bpy.data.worlds.new('ReviewWorld'); common.workbench_clay(scene)
mesh.color=(.52,.55,.57,1); scene.display.shading.color_type='OBJECT'
common.render_views(str(P/'review/geometry_v2'),1.2,max(2.7,(co[:,0].max()-co[:,0].min())*1.15*1000/700),views=('front','left','back','right','three_quarter'),resolution=(700,1000))
print('GEOMETRY',report['vertices'],report['triangles'],'parts',[(len(x),np.round(co[x].mean(0),3).tolist()) for x in parts[:20]])
