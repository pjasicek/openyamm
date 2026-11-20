import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from rebake_maps import bake
sel=json.loads((P/'review/reduction_selected.json').read_text());out=P/'review/palm_fit';out.mkdir(exist_ok=True);work=P/'work/palm_fit';work.mkdir(exist_ok=True);report={}
for level in [1,2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];shield=bpy.data.objects['LeafShield'];sc=bpy.context.scene;me=body.data;names=[g.name for g in body.vertex_groups];weights=np.array([sum(g.weight for g in v.groups if names[g.group]=='B_L_Hand')for v in me.vertices]);palm=set(np.where(weights>.7)[0]);faces=[tuple(f.vertices)for f in me.polygons if all(i in palm for i in f.vertices)];assert faces
 M=rig.data.bones['LeafShield'].matrix_local.inverted();vc=[M@v.co for v in shield.data.vertices];sf=[tuple(f.vertices)for f in shield.data.polygons if all(abs(vc[i].x)<.09 and abs(vc[i].y-.045)<.022 and abs(vc[i].z-.26)<.021 for i in f.vertices)];tree=BVHTree.FromPolygons(vc,sf);probes=[tree.find_nearest(Vector((x,.045+.011*np.cos(a),.26+.011*np.sin(a))))[0]for x in np.linspace(-.06,.06,49)for a in np.arange(32)*np.pi/16];act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(0);history=[];before=np.array([tuple(v.co)for v in me.vertices])
 for iteration in range(6):
  bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();iv=rig.pose.bones['LeafShield'].matrix.inverted();pts=[iv@v.co for v in mm.vertices];ev.to_mesh_clear();ptree=BVHTree.FromPolygons(pts,faces);hits=[ptree.find_nearest(q)for q in probes];j=min(range(len(probes)),key=lambda i:hits[i][3]);hit,normal,index,dist=hits[j];history.append(dist*1000)
  if dist<.002:break
  local=(probes[j]-hit).normalized()*(dist-.0015);world=rig.pose.bones['LeafShield'].matrix.to_3x3()@local;rest=rig.data.bones['B_L_Hand'].matrix_local.to_3x3()@rig.pose.bones['B_L_Hand'].matrix.to_3x3().inverted()@world
  for v in me.vertices:
   weight=max(0,min(1,(weights[v.index]-.35)/.65))
   if weight:v.co+=rest*weight
  me.update()
 assert history[-1]<2,history
 report[str(level)]={'palm_gap_iterations_mm':history,'max_rest_vertex_move_mm':float(np.linalg.norm(np.array([tuple(v.co)for v in me.vertices])-before,axis=1).max()*1000)}
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 with bpy.data.libraries.load(str(P/'work/accepted_master.blend'))as(src,dst):dst.meshes=['Body']
 ref=bpy.data.objects.new('BakeReference',dst.meshes[0]);bpy.context.collection.objects.link(ref);ref.hide_render=True;material_ids=[f.material_index for f in me.polygons];body.data.materials.clear()
 for i,name in enumerate(['Natf_A','NatfHead_A']):
  mat=ref.data.materials[i];old=bpy.data.materials.get(name)
  if old and old!=mat:old.name=name+'_Unused'
  mat.name=name;body.data.materials.append(mat)
 for f,idx in zip(me.polygons,material_ids):f.material_index=idx
 maps=bake(body,ref,out,f'lod{level}',size=1024 if level==1 else 512);bpy.data.objects.remove(ref,do_unlink=True);path=work/f'lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));row=sel['Body'][str(level)];row['pre_contact_blend']=row['blend'];row['blend']=str(path.relative_to(P));row['maps']=maps;row['contact_fit']=report[str(level)];print('PALM_FIT',level,report[str(level)],flush=True)
(P/'review/final/palm_fit.json').write_text(json.dumps(report,indent=2));(P/'review/reduction_selected.json').write_text(json.dumps(sel,indent=2))
