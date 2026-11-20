"""Inspect owned Smart Topology returns in metres, with topology records and CPU clay views.
Preserves raw downloads and geometry; only applies the GLB transform and a uniform scale/floor offset.
"""
import bpy, bmesh, sys, os, json, hashlib, math
from pathlib import Path
import numpy as np
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
sex = sys.argv[sys.argv.index('--')+1]
assert sex in ('m','f')
clean_review = 'clean' in sys.argv[sys.argv.index('--')+2:]
source = P/'work'/f'kept_{sex}_clean_v1.blend' if clean_review else P/'meshy'/f'kept_{sex}_smart_v1/model_urls_glb.glb'
out = P/'review/geometry'/(sex+'_clean' if clean_review else sex)
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
if clean_review:
    bpy.ops.wm.open_mainfile(filepath=str(source))
else:
    bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.data.objects if o.type=='MESH']
assert len(meshes)==1 and not any(o.type=='ARMATURE' for o in bpy.data.objects)
body = meshes[0]
body.name = body.data.name = 'Body'
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co = np.array([v.co[:] for v in body.data.vertices])
lo,hi = co.min(0),co.max(0)
scale = 1.7/(hi[2]-lo[2])
# Meshy already faces glTF +Z (= Blender -Y); keep the input yaw.
offset = np.array([(lo[0]+hi[0])/2,0,lo[2]])
co = (co-offset)*scale
body.data.vertices.foreach_set('co',co.ravel());body.data.update()
me = body.data
adj = [[] for _ in me.vertices]
for edge in me.edges:
    a,b=edge.vertices;adj[a].append(b);adj[b].append(a)
remaining=set(range(len(co)));components=[]
while remaining:
    stack=[next(iter(remaining))];comp=[]
    while stack:
        i=stack.pop()
        if i not in remaining:continue
        remaining.remove(i);comp.append(i);stack.extend(adj[i])
    components.append(comp)
components.sort(key=len,reverse=True)
piece=np.zeros(len(co),dtype=np.int32)
rows=[]
for i,ids in enumerate(components):
    piece[ids]=i
    rows.append({'piece':i,'vertices':len(ids),'min':co[ids].min(0).tolist(),'max':co[ids].max(0).tolist()})
if 'piece' in me.attributes:me.attributes.remove(me.attributes['piece'])
if 'orig_co' in me.attributes:me.attributes.remove(me.attributes['orig_co'])
me.attributes.new('piece','INT','POINT').data.foreach_set('value',piece)
me.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
face_keys=[tuple(sorted(v.index for v in face.verts)) for face in bm.faces]
report={'source':str(source.relative_to(P)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'height_m':1.7,'scale_applied':float(scale),'offset_before_scale':offset.tolist(),
        'bounds_min':co.min(0).tolist(),'bounds_max':co.max(0).tolist(),
        'vertices':len(co),'triangles':sum(len(f.vertices)-2 for f in me.polygons),
        'parts':rows,'boundary_edges':sum(e.is_boundary for e in bm.edges),
        'nonmanifold_edges_excluding_boundary':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
        'loose_vertices':sum(not v.link_faces for v in bm.verts),
        'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
        'duplicate_faces':len(face_keys)-len(set(face_keys)),
        'geometry_changes':'Rigid transform, uniform normalization to 1.7 m, floor/x centering only; no vertex removal, welding, smoothing or reduction.'}
for row in rows:
    faces=[f for f in bm.faces if piece[f.verts[0].index]==row['piece']]
    row['triangles']=sum(len(f.verts)-2 for f in faces)
    edges={e for f in faces for e in f.edges}
    row['boundary_edges']=sum(e.is_boundary for e in edges)
    row['signed_volume']=sum(float(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)))/6 for f in faces)
assert np.isfinite(co).all() and abs(co[:,2].max()-1.7)<1e-6 and abs(co[:,2].min())<1e-6
assert report['duplicate_faces']==0 and report['degenerate_faces']==0 and report['loose_vertices']==0
bm.free()
(out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
mat=bpy.data.materials.new('InspectionClay');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(0.45,0.48,0.5,1);bsdf.inputs['Roughness'].default_value=.8
me.materials.clear();me.materials.append(mat)
for poly in me.polygons:poly.use_smooth=True
if not clean_review:bpy.ops.wm.save_as_mainfile(filepath=str(P/'work'/f'kept_{sex}_ingested_v1.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Review');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for pos,power in [((3,-4,5),500),((-3,-2,3),300),((0,4,4),250)]:
    data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.size=4
    obj=bpy.data.objects.new('Softbox',data);scene.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector((0,0,.9))-obj.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.cameras.new('ReviewCamera');camera.type='ORTHO'
cam=bpy.data.objects.new('ReviewCamera',camera);scene.collection.objects.link(cam);scene.camera=cam
views=[(n,(0,0,.85),a,1.95,(512,768)) for n,a in [('front',0),('left',90),('back',180),('right',-90),('quarter',35)]]
views += [(n,(0,0,1.52),a,.47,(640,640)) for n,a in [('head_front',0),('head_side',90),('head_back',180)]]
for side,sg in [('L',1),('R',-1)]:
    hand=co[(co[:,0]*sg>co[:,0].max()*.73)&(co[:,2]<1.1)]
    centre=(hand.min(0)+hand.max(0))/2
    views += [(f'hand_{side}_{name}',tuple(centre),angle,.32,(640,640)) for name,angle in [('front',0),('back',180),('side',90*sg)]]
if 'focus' in sys.argv:
    views=[v for v in views if v[0] in ('front','left','quarter','head_front','head_side')]
for name,target,angle,zoom,res in views:
    target=Vector(target);a=math.radians(angle);cam.location=target+Vector((5*math.sin(a),-5*math.cos(a),0))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camera.ortho_scale=zoom
    scene.render.resolution_x,scene.render.resolution_y=res;scene.render.filepath=str(out/f'{name}.png')
    bpy.ops.render.render(write_still=True)
print('GEOMETRY',sex,json.dumps({k:report[k] for k in ['vertices','triangles','boundary_edges','nonmanifold_edges_excluding_boundary','degenerate_faces']}),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
