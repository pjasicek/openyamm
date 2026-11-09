import bpy,sys,numpy as np,json
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'scripts'),str(P.parent/'claude_shared/gates')];import common,reduction_common as C,run_gates as G
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/selected_lod0.blend'));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];print('MODIFIERS',[(m.name,m.type,m.use_deform_preserve_volume,m.use_bone_envelopes,m.use_vertex_groups,m.object.name)for m in o.modifiers if m.type=='ARMATURE'],flush=True)
g=G.Glb(P/'export/mm6_mer1.glb');m=G.load_meshes(g)[0];kd=KDTree(len(o.data.vertices))
for v in o.data.vertices:kd.insert(v.co,v.index)
kd.balance();mapping=np.array([kd.find(c)[1]for c in m.rest]);report=[]
for role,t in [('Attack',.4),('Death',1.3)]:
 C.activate(role,t);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();a=next(a for a in g.doc['animations']if a['name']==role);pose=g.pose(a,np.array([t]))[0];gc=m.posed(pose);err=np.linalg.norm(gc-coords[mapping],axis=1);j=int(np.argmax(err));print('POSE DIFF',role,'max',err[j],'p99',np.percentile(err,99),'rest',m.rest[j],'blend',coords[mapping[j]],'glb',gc[j],flush=True)
 rows=[]
 for n in ['B_Pelvis','B_Spine2','B_L_UpperArm','B_L_Forearm','B_L_Hand','Cloak_0_0']:
  rows.append([n,float(abs(np.array(r.pose.bones[n].matrix)-pose[g.names[n]]).max())])
 print('JOINT DIFF',rows,flush=True);common.workbench_clay(bpy.context.scene,True);bpy.context.scene.display.shading.show_specular_highlight=False;common.render_views(str(P/'review/round3'/f'selected_{role}'),1.15,1.2,views=('front','left'),resolution=(800,900))
