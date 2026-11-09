"""Dense source/export pose parity and deformation/contact measurements on the delivered body GLB."""
from pathlib import Path
import bpy,json,numpy as np,math
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/centaur_master.blend'))
source=bpy.data.objects['Body'];sr=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=48
sa={a.name:a for a in bpy.data.actions};objects=set(bpy.data.objects);actions=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_centaur.glb'))
rig=next(o for o in bpy.data.objects if o not in objects and o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o not in objects and o.type=='MESH')
ea={a.name.split('.')[0]:a for a in bpy.data.actions if a not in actions}
for r in (sr,rig):
    for track in r.animation_data.nla_tracks:track.mute=True
rest=np.array([(body.matrix_world@v.co)[:]for v in body.data.vertices]);tree=KDTree(len(source.data.vertices))
for v in source.data.vertices:tree.insert(source.matrix_world@v.co,v.index)
tree.balance();mapping=[tree.find(v.co)[1]for v in body.data.vertices]
assert max(tree.find(v.co)[2]for v in body.data.vertices)<1e-5
edges=np.array([e.vertices[:]for e in body.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
names=[g.name for g in body.vertex_groups];regions={}
visible=np.array([sum(g.weight for g in v.groups if names[g.group]=='Arrow')<.5 for v in body.data.vertices])
for region,parts in [('hands',('Hand','Thumb','Index','Middle','Ring','Pinky')),('arms',('Arm',)),('skin',('Horse','Spine','Chest','Head','Neck','Arm','Hand','Front','Hind','Thumb','Index','Middle','Ring','Pinky'))]:
    mask=np.array([sum(g.weight for g in v.groups if any(n in names[g.group]for n in parts))>.5 for v in body.data.vertices]);regions[region]=mask[edges].all(1)&(length>.003)
def points(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([(ev.matrix_world@v.co)[:]for v in m.vertices]);ev.to_mesh_clear();return p
report={};fail=[]
for name,info in json.loads((P/'work/clips.json').read_text()).items():
    sr.animation_data.action=sa[name];sr.animation_data.action_slot=sa[name].slots[0];rig.animation_data.action=ea[name];rig.animation_data.action_slot=ea[name].slots[0]
    n=info['frames']-1;errors=[];ratios=[];minz=[];contacts=[];first=None;last=None;worst={}
    for f in np.linspace(0,n,97):
        sc.frame_set(int(f),subframe=float(f%1));p=points(body);s=points(source)[mapping];delta=np.linalg.norm(p-s,axis=1);errors.append(float(delta.max()));
        if errors[-1]>=max(errors):worst={'frame':float(f),'vertex':int(delta.argmax()),'source_vertex':int(mapping[delta.argmax()]),'weights':{names[g.group]:g.weight for g in body.data.vertices[int(delta.argmax())].groups}}
        minz.append(float(p[visible,2].min()));ratios.append(np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)/np.maximum(length,1e-9))
        if first is None:first=p.copy()
        last=p
        if name in ('Walking','Running'):
            run=name=='Running';duty=.52 if run else .62;stride=1.15 if run else .7
            for side,phase in [('L',0),('R',.5)]:
                for front in (True,False):
                    u=(f/n+phase+(0 if front else .5))%1
                    if u>=duty:continue
                    bone=('Front'if front else'Hind')+'Hoof_'+side;target=sr.data.bones[bone].head_local.copy();target.y+=-stride/2+stride*u/duty
                    contacts.append(float(((rig.matrix_world@rig.pose.bones[bone].head)-target).length))
    ratios=np.array(ratios);result={'samples':97,'max_source_export_error_m':max(errors),'minimum_z_m':min(minz),'endpoint_delta_m':float(np.linalg.norm(last-first,axis=1).max()),'max_stance_error_m':max(contacts,default=0)}
    for k,m in regions.items():result[k]={'edge_p99':float(np.percentile(ratios[:,m],99)),'edge_max':float(ratios[:,m].max())}
    mi=np.where(regions['skin'])[0];fr,ix=np.unravel_index(np.argmax(ratios[:,mi]),ratios[:,mi].shape);ei=mi[ix]
    result['worst_skin_edge']={'frame':float(np.linspace(0,n,97)[fr]),'rest_length_m':float(length[ei]),'vertices':[{'position':rest[v].tolist(),'weights':{names[g.group]:g.weight for g in body.data.vertices[v].groups}}for v in edges[ei]]}
    result['worst_export']=worst;report[name]=result;print(name,json.dumps(result),flush=True)
    if max(errors)>.003:fail.append(name+' export mismatch')
    if result['arms']['edge_p99']>2 or result['hands']['edge_max']>4.5:fail.append(name+' deformation')
    if name in ('Standing','Walking','Running','Dead')and result['endpoint_delta_m']>.001:fail.append(name+' loop seam')
    if contacts and max(contacts)>.012:fail.append(name+' stance slip')
report['failures']=fail;(P/'review/export_probe.json').write_text(json.dumps(report,indent=2)+'\n');assert not fail,fail
