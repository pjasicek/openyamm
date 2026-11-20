"""Correct duplicated dorsal rows and the over-thick tail, preserving the returned body topology."""
from pathlib import Path
import bpy, bmesh, json, sys
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import common
P=Path(common.PROJECT)
paid_positions=P/'work/paid_rig_input_positions.npy'
if not paid_positions.exists():
    bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
    np.save(paid_positions,np.array([tuple(v.co) for v in bpy.data.objects['Body'].data.vertices]))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
# The source has one dorsal row; the return added two complete flanking rows.
extra_spines=[1,2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,19,20]
for idx in extra_spines:
    bpy.data.objects.remove(parts.pop(f'P{idx:02d}'),do_unlink=True)
body=parts['P00'];bm=bmesh.new();bm.from_mesh(body.data)
boundary=[e for e in bm.edges if e.is_boundary]
assert len(boundary)==5 and all(1.33<v.co.z<1.35 for e in boundary for v in e.verts)
new=bmesh.ops.holes_fill(bm,edges=boundary,sides=5)['faces']
bmesh.ops.triangulate(bm,faces=new)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data);bm.free()
path=np.array([[-.009,-.18,.95],[-.009,-.055,.78],[-.009,.005,.65],[-.007,-.005,.55],
               [-.004,-.05,.38],[-.001,-.015,.24],[0,.08,.15],[0,.23,.14],
               [0,.38,.21],[0,.49,.34],[0,.58,.48]])
seg=path[1:]-path[:-1];lengths=np.linalg.norm(seg,axis=1);cumulative=np.r_[0,np.cumsum(lengths)]
records=[]
for name,obj in parts.items():
    co=np.array([tuple(v.co) for v in obj.data.vertices]);closest=np.zeros_like(co);distance=np.full(len(co),np.inf);along=np.zeros(len(co))
    for i,(start,d) in enumerate(zip(path[:-1],seg)):
        t=np.clip((co-start)@d/(d@d),0,1);c=start+t[:,None]*d
        dist=np.linalg.norm(co-c,axis=1);use=dist<distance
        distance[use]=dist[use];closest[use]=c[use];along[use]=(cumulative[i]+t[use]*lengths[i])/cumulative[-1]
    # Fade through the existing sacral attachment; the arrow tip retains its shape.
    w=np.clip((co[:,1]+.18)/.10,0,1)*np.clip((.95-co[:,2])/.16,0,1)
    w*=np.clip((.16-np.abs(co[:,0]+.009))/.04,0,1)
    w*=1-np.clip((along-.85)/.15,0,1)
    w=w*w*(3-2*w)
    co=closest+(co-closest)*(1-.55*w[:,None])
    co+=np.array([.009,.35,0])
    obj.data.vertices.foreach_set('co',co.ravel());obj.data.update()
    obj.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(name[1:])]*len(co))
    obj.data.attributes.new('tail_weight','FLOAT','POINT').data.foreach_set('value',w)
    records.append({'piece':int(name[1:]),'vertices':len(co),'tail_vertices':int(sum(w>.5))})
    obj.data.materials.clear()
    mat=bpy.data.materials.new(name+'_provisional');mat.use_nodes=True
    color=(.11,.32,.09,1) if int(name[1:])==0 else (.52,.48,.28,1)
    if int(name[1:]) in (26,27):color=(.8,.65,.03,1)
    img=bpy.data.images.new(name+'_provisional',width=4,height=4,alpha=True)
    img.pixels[:]=list(color)*16;img.pack()
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img
    bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=.8;mat.diffuse_color=color
    obj.data.materials.append(mat)
    if not obj.data.uv_layers:obj.data.uv_layers.new(name='UVMap')
    for uv in obj.data.uv_layers.active.data:uv.uv=(.5,.5)
    for f in obj.data.polygons:f.material_index=0;f.use_smooth=True
for obj in bpy.data.objects:obj.select_set(obj.type=='MESH')
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Body'
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',np.load(paid_positions).ravel())
assert abs(co[:,2].min())<.0001 and abs(co[:,2].max()-1.7)<.0001
(P/'export').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/gog_clean_v2.glb'),use_selection=True,export_format='GLB',
 export_yup=True,export_animations=False,export_skins=False,export_attributes=False,export_materials='EXPORT')
(P/'work/cleanup.json').write_text(json.dumps({'removed_duplicate_spines':extra_spines,'sealed_boundary':'5-edge shoulder hole',
 'tail_radial_scale':.45,'tail_path':(path+[.009,.35,0]).tolist(),'parts':records,
 'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'provisional_texture_only':True},indent=2)+'\n')
scene=bpy.context.scene;common.workbench_clay(scene);scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.65,.65,.65)
common.render_views(str(P/'review/clean_v2'),.85,2.1,views=('front','left','back','three_quarter'),resolution=(700,900))
print('CLEAN',len(co),'vertices',sum(len(f.vertices)-2 for f in body.data.polygons),'triangles')
