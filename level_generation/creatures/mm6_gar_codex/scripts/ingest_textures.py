"""Transfer returned UVs by verified triangle correspondence, preserving all rig/animation data."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_skin.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
report={}
(P/'textures').mkdir(exist_ok=True)
for name in ['Body','Head']:
 target=bpy.data.objects[name]
 bm=bmesh.new();bm.from_mesh(target.data)
 if name=='Body':
    # Meshy collapsed this 90-micrometre boolean seam edge, removing its two sliver triangles.
    a=Vector((-.4570100009441376,-.12425065040588379,.9754995703697205))
    b=Vector((-.4570857584476471,-.12420471012592316,.9754924774169922))
    va=min(bm.verts,key=lambda v:(v.co-a).length);vb=min(bm.verts,key=lambda v:(v.co-b).length)
    assert va!=vb and (va.co-a).length<1e-7 and (vb.co-b).length<1e-7 and (va.co-vb.co).length<.0001
    bmesh.ops.pointmerge(bm,verts=[va,vb],merge_co=a)

 if name=='Head':
    seen=set();duplicates=[]
    for f in bm.faces:
        key=tuple(sorted(tuple(round(x,7) for x in v.co) for v in f.verts))
        if key in seen:duplicates.append(f)
        else:seen.add(key)
    print('HEAD_DUPLICATE_FACES',len(duplicates))
    if duplicates:bmesh.ops.delete(bm,geom=duplicates,context='FACES_ONLY')
 degenerate=[f for f in bm.faces if f.calc_area()<(1e-11 if name=='Head' else 1e-14)]
 if degenerate:bmesh.ops.delete(bm,geom=degenerate,context='FACES_ONLY')
 bm.to_mesh(target.data);bm.free()
 print('REMOVED_EXPORT_DEGENERATES',name,len(degenerate),'smallest retained',[p.area for p in sorted(target.data.polygons,key=lambda p:p.area)[:5]])
 job=P/f'meshy/{name.lower()}_texture_v1';before=set(bpy.data.objects)
 bpy.ops.import_scene.gltf(filepath=str(job/'model_urls_glb.glb'))
 new=set(bpy.data.objects)-before;source=next(o for o in new if o.type=='MESH')
 S=np.array([tuple(source.matrix_world@v.co) for v in source.data.vertices]);T=np.array([v.co[:] for v in target.data.vertices])
 scale=np.ptp(T,axis=0).max()/np.ptp(S,axis=0).max();offset=(T.max(0)+T.min(0))/2-(S.max(0)+S.min(0))/2*scale;S=S*scale+offset
 print('RETURN_FACES',name,len(source.data.polygons),'master',len(target.data.polygons))
 tree=kdtree.KDTree(len(source.data.polygons))
 for poly in source.data.polygons:tree.insert(Vector(S[list(poly.vertices)].mean(0)),poly.index)
 tree.balance();used=set();maxcorner=0;maxcentre=0
 assert len(target.data.polygons)==len(source.data.polygons),(name,len(target.data.polygons),len(source.data.polygons))
 for uv in list(target.data.uv_layers):target.data.uv_layers.remove(uv)
 destuv=target.data.uv_layers.new(name='UVMap').data;srcuv=source.data.uv_layers.active.data
 for poly in target.data.polygons:
    _,i,d=tree.find(Vector(T[list(poly.vertices)].mean(0)));assert i not in used,(name,i);used.add(i);maxcentre=max(maxcentre,d);sp=source.data.polygons[i]
    for li in poly.loop_indices:
        pt=T[target.data.loops[li].vertex_index];sl=min(sp.loop_indices,key=lambda k:np.linalg.norm(S[source.data.loops[k].vertex_index]-pt))
        maxcorner=max(maxcorner,float(np.linalg.norm(S[source.data.loops[sl].vertex_index]-pt)));destuv[li].uv=srcuv[sl].uv
 assert maxcorner<.0002 and maxcentre<.0002,(name,maxcorner,maxcentre)
 target.data.materials.clear();mat=bpy.data.materials.new('Gargoyle'+name);mat.use_nodes=True;target.data.materials.append(mat);bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.85
 img=bpy.data.images.load(str((job/'texture_urls_0_base_color.png').resolve()),check_existing=True);tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.nodes.active=tex
 # UV/3D correspondence is also the source of region and material-class masks.
 target.data.calc_loop_triangles();uv=target.data.uv_layers.active.data
 u=[];xyz=[];part=[]
 for tri in target.data.loop_triangles:
    u.append([uv[li].uv[:] for li in tri.loops]);points=[target.data.vertices[vi].co[:] for vi in tri.vertices];xyz.append(points)
    wing=sum(sum(g.weight for g in target.data.vertices[vi].groups if target.vertex_groups[g.group].name.startswith('W_')) for vi in tri.vertices)/3
    part.append(3 if wing>.35 else 1)
 np.savez(P/f'work/{name.lower()}_uv3d.npz',uv=np.array(u),xyz=np.array(xyz),part=np.array(part))
 report[name]={'collapsed_boolean_seam_edges':1 if name=='Body' else 0,'faces':len(used),'max_corner_error_m':maxcorner,'max_centroid_error_m':maxcentre,'return_scale':scale,'return_offset':offset.tolist()}
 for o in new:bpy.data.objects.remove(o,do_unlink=True)
 for poly in target.data.polygons:poly.use_smooth=True
(P/'work/texture_correspondence.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_source.blend'))
scene=bpy.context.scene;common.workbench_clay(scene,textured=True)
common.render_views(str(P/'review/textured_source'),1.5,3.3,views=('front','left','back','three_quarter'),resolution=(900,1200))
common.render_views(str(P/'review/textured_source_head'),1.68,.60,views=('front','left','three_quarter'),resolution=(900,900),target=(0,-.03))
print('TEXTURE_TRANSFER',report)
