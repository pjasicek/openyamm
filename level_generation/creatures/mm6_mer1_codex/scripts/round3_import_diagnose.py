import bpy,sys,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
bpy.ops.wm.read_factory_settings(use_empty=True);path=P/'export/mm6_mer1_portable_a.glb';bpy.ops.import_scene.gltf(filepath=str(path));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');obs=[o for o in bpy.data.objects if o.type=='MESH'];print('IMPORTED OBJECTS',[(o.name,len(o.data.vertices),[(m.name,m.type)for m in o.modifiers])for o in obs],flush=True);o=max(obs,key=lambda x:len(x.data.vertices));print('FPS',bpy.context.scene.render.fps,'NLAS',[(t.name,t.mute)for t in r.animation_data.nla_tracks],flush=True);g=G.Glb(path);m=G.load_meshes(g)[0];kd=KDTree(len(o.data.vertices))
for v in o.data.vertices:kd.insert(o.matrix_world@v.co,v.index)
kd.balance();found=[kd.find(c)for c in m.rest];mapping=np.array([x[1]for x in found]);print('RESTMATCH',max(x[2]for x in found),flush=True)
for role,t in [('Attack',.4),('Death',1.3)]:
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==role);r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=t*bpy.context.scene.render.fps;bpy.context.scene.frame_set(int(f),subframe=f%1);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=np.array([o.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear();ga=next(a for a in g.doc['animations']if a['name']==role);pose=g.pose(ga,np.array([t]))[0];gc=m.posed(pose);err=np.linalg.norm(gc-coords[mapping],axis=1);j=int(np.argmax(err));print('IMPORT POSE',role,err.max(),np.percentile(err,99),m.rest[j],coords[mapping[j]],gc[j],flush=True)
 print('JOINTS',[(n,float(abs(np.array(r.matrix_world@r.pose.bones[n].matrix)[:3,3]-pose[g.names[n],:3,3]).max()))for n in ['B_Pelvis','B_Spine2','B_L_UpperArm','B_L_Forearm','B_L_Hand']],flush=True)
