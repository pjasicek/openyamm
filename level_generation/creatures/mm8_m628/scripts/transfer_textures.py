"""Transfer only UV corners after a complete one-to-one triangle and position check of all texture returns."""
import bpy,json,sys,itertools
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_upload.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
piece=np.array([x.value for x in me.attributes['piece'].data]);head=np.array([x.value for x in me.attributes['head'].data])
rest=np.array([tuple(v.co)for v in me.vertices]);ib=rig.data.bones['Bow'].matrix_local.inverted()
report={}
for kind,layer in [('body','UVMap'),('head','HeadUV'),('bow','BowUV')]:
    def keep(f):
        pid=piece[f.vertices[0]]
        return pid<4000 if kind=='body'else bool(head[f.index])if kind=='head'else pid in [4000,4003,4004]
    target=[f for f in me.polygons if keep(f)];T=rest.copy()
    if kind=='bow':
        for i in np.where(piece>=4000)[0]:T[i]=rest[i]+np.array([.25,0,-.30])if piece[i]==4003 else np.array(ib@Vector(rest[i]))
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/f'meshy/{kind}_retexture_v1/model_urls_glb.glb'))
    objects=[o for o in bpy.data.objects if o not in before and o.type=='MESH'];assert len(objects)==1
    ob=objects[0];src=ob.data
    assert len(src.polygons)==len(target)-(1 if kind=='body'else 0),(kind,len(src.polygons),len(target))
    S=np.array([tuple(ob.matrix_world@v.co)for v in src.vertices]);sub=T[sorted({v for f in target for v in f.vertices})]
    scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();offset=(sub.max(0)+sub.min(0))*.5-(S.max(0)+S.min(0))*.5*scale;S=S*scale+offset
    tree=kdtree.KDTree(len(src.polygons))
    for f in src.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
    tree.balance();used=set();worst=0.;uv=me.uv_layers[layer].data;suv=src.uv_layers.active.data;degenerate=0;patched=[]
    for f in target:
        assert len(f.vertices)==3
        tp=T[list(f.vertices)];c=Vector(tp.mean(0));candidates=tree.find_range(c,.00015);best=None
        for _,i,d in candidates:
            if i in used:continue
            sf=src.polygons[i];assert len(sf.vertices)==3
            sp=S[list(sf.vertices)]
            for order in itertools.permutations(range(3)):
                error=float(np.linalg.norm(tp-sp[list(order)],axis=1).max())
                if best is None or error<best[0]:best=(error,i,order)
        if best is None:
            # Meshy removed this specific rib face. Keep our geometry and give it a dedicated bone-painted chart.
            expected=np.array([[.0876716301,-.0314215124,1.1784129143],[.0863519683,-.0452539772,1.1932272911],
                [.0796028376,-.0525090918,1.1954219341]])
            assert kind=='body'and min(np.linalg.norm(tp-expected[list(o)],axis=1).max()for o in itertools.permutations(range(3)))<1e-6,(kind,f.index)
            for li,xy in zip(f.loop_indices,[(.004,.49),(.016,.49),(.01,.51)]):uv[li].uv=xy
            patched.append({'face':f.index,'piece':int(piece[f.vertices[0]]),'area_m2':float(f.area),'method':'Dedicated chart in reserved 2 percent left strip; bone albedo and local AO.'})
            continue
        assert best[0]<.00015,(kind,f.index,best)
        error,i,order=best;used.add(i);worst=max(worst,error);sf=src.polygons[i]
        for li,j in zip(f.loop_indices,order):
            xy=suv[sf.loop_indices[j]].uv.copy()
            if kind=='body':xy.x=.02+.98*xy.x
            uv[li].uv=xy
        tri=np.array([tuple(uv[li].uv)for li in f.loop_indices]);area=abs(np.linalg.det(np.stack([tri[1]-tri[0],tri[2]-tri[0]])))*.5
        if area<1e-12:degenerate+=1
    assert len(used)==len(src.polygons)
    assert degenerate==0,(kind,degenerate)
    assert len(patched)==(1 if kind=='body'else 0)
    report[kind]={'faces':len(target),'returned_faces_matched_once':len(used),'local_patches':patched,
        'maximum_corner_error_m':worst,'uniform_scale':float(scale),'translation':offset.tolist(),'degenerate_uv_triangles':degenerate,
        'image_transform':{'u_scale':.98,'u_offset':.02}if kind=='body'else None}
    for o in list(bpy.data.objects):
        if o not in before:bpy.data.objects.remove(o,do_unlink=True)
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
(P/'work/texture_correspondence.json').write_text(json.dumps(report,indent=2));print('UV CORRESPONDENCE',report)
