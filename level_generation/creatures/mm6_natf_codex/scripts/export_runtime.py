"""Export the selected measured meshes with one common rig and the nine accepted actions."""
import bpy,json,math,numpy as np,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
sel=json.loads((P/'review/reduction_selected.json').read_text());out=P/'export';out.mkdir(exist_ok=True);roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];info={'lods':[],'clips':{}}
def neutral(r):
 r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/sel['Body'][str(level)]['blend']));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;neutral(rig)
 # Non-deforming landmark carries the measured irregular-hem opening frame.
 if 'HemOpening'not in rig.data.bones:
  bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new('HemOpening');b.head=(0,0,0);b.tail=(0,1,0);bpy.ops.object.mode_set(mode='OBJECT')
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/accepted_master.blend'))as(src,dst):dst.actions=roles.copy()
 for a in dst.actions:a.use_fake_user=True
 maps=sel['Body'][str(level)]['maps'].copy()
 for part in ['ForearmBlade','LeafShield']:
  old=bpy.data.objects[part]
  if (P/sel[part][str(level)]['blend']).resolve()!=Path(bpy.data.filepath).resolve():
   with bpy.data.libraries.load(str(P/sel[part][str(level)]['blend']))as(src,dst):dst.meshes=[part]
   assert len(dst.meshes)==1 and dst.meshes[0]is not None,(part,src.meshes)
   old.data=dst.meshes[0]
  old.vertex_groups.clear();old.vertex_groups.new(name=part).add(list(range(len(old.data.vertices))),1,'REPLACE');maps+=sel[part][str(level)]['maps']
 objects=[body,bpy.data.objects['ForearmBlade'],bpy.data.objects['LeafShield']]
 for ob in objects:
  ob.hide_render=False;ob.hide_set(False)
  for uv in list(ob.data.uv_layers):
   if uv.name!='UVMap':ob.data.uv_layers.remove(uv)
  for mat in ob.data.materials:
   base=mat.get('source_material',mat.name);stable=base if level==0 else base.replace('_A',f'_L{level}_A');old=bpy.data.materials.get(stable)
   if old and old!=mat:old.name=stable+'_Unused'
   mat.name=stable
   # Export defaults prevent unsupported specular/IOR extensions.
   bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['IOR'].default_value=1.5;bs.inputs['Specular IOR Level'].default_value=.5;bs.inputs['Specular Tint'].default_value=(1,1,1,1)
  for v in ob.data.vertices:
   weights=[(g.group,g.weight)for g in v.groups if ob.vertex_groups[g.group].name in rig.data.bones and g.weight>0];total=sum(w for _,w in weights);assert total>0
   for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
   for i,w in weights:ob.vertex_groups[i].add([v.index],w/total,'REPLACE')
  assert max(abs(sum(g.weight for g in v.groups)-1)for v in ob.data.vertices)<1e-5
 counts={ob.name:sum(len(f.vertices)-2 for f in ob.data.polygons)for ob in objects};info['lods'].append({'level':level,'triangles':counts,'maps':maps});bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/final_lod{level}.blend'))
 if level==0:
  info['bones']=len(rig.data.bones)
  for role in roles:
   act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];ts=sorted(set(list(np.arange(0,act.frame_range[1]/sc.render.fps+.00001,1/48))+[act.frame_range[1]/sc.render.fps]));bounds=[];tr=[];stride={s:[]for s in 'LR'}
   for t in ts:
    frame=t*sc.render.fps;sc.frame_set(int(frame),subframe=float(frame%1));lo,hi=common.world_bounds(objects);bounds.append([list(lo),list(hi)]);M=rig.pose.bones['ForearmBlade'].matrix;tip=M@Vector((.1432828,0,.65));axis=(M.to_3x3()@Vector((0,0,1))).normalized();edge=(M.to_3x3()@Vector((-1,0,0))).normalized();hand=rig.pose.bones['B_R_Hand'].head;tr.append({'t':t,'tip':list(tip),'axis':list(axis),'edge':list(edge),'hand':list(hand)})
    for s in 'LR':stride[s].append(rig.pose.bones[f'B_{s}_Foot'].head.y)
   row={'duration':float(ts[-1]),'bounds_m':np.array(bounds)[:,0].min(0).tolist()+np.array(bounds)[:,1].max(0).tolist()}
   if role=='Standing':
    lo,hi=common.world_bounds([body]);info['standing_height_m']=hi.z-lo.z;info['runtime_scale']=177.099241/(hi.z-lo.z)
   if role=='Walking':info['stride_length_m']=float(np.mean([2*(max(v)-min(v))for v in stride.values()]))
   if role in ['Attack','Cast']:
    (P/f'review/final/{role.lower()}_motion_trace.json').write_text(json.dumps(tr,indent=2));tt=np.array(ts);tip=np.array([r['tip']for r in tr]);vel=np.diff(tip,axis=0)/np.diff(tt)[:,None];axes=np.array([r['axis']for r in tr]);edges=np.array([r['edge']for r in tr]);speed=np.linalg.norm(vel,axis=1);fw=-axes[1:,1]
    if role=='Attack':
     transverse=vel-axes[1:]*np.sum(vel*axes[1:],axis=1)[:,None];lead=np.sum(edges[1:]*transverse,axis=1)/np.maximum(np.linalg.norm(transverse,axis=1),1e-9);valid=(fw>.5)&(lead>.5)&(tt[1:]>.2)&(-vel[:,1]>0);assert valid.any();i=int(np.argmax(np.where(valid,speed,-1)))+1;v=vel[i-1];u=v/np.linalg.norm(v);side=v-axes[i]*np.dot(v,axes[i]);row.update(impact=float((tt[i-1]+tt[i])/2),tip_speed_mps=float(speed[i-1]),target_dot=float(fw[i-1]),edge_lead_dot=float(np.dot(edges[i],side/np.linalg.norm(side))),edge_share=float(abs(np.dot(edges[i],u))));assert row['edge_lead_dot']>.5
    else:
     hand=np.array([r['hand']for r in tr]);eligible=(tt>.2)&(tt<ts[-1]-.2);i=int(np.argmin(np.where(eligible,hand[:,1],1e6)));row.update(impact=float(tt[i]),launch_socket='B_R_Hand')
   info['clips'][role]=row
  neutral(rig);bpy.ops.wm.save_as_mainfile(filepath=str(out/'mm6_natf.blend'))
 # Join only for glTF; the fitted authoring masters retain separate inspectable props.
 bpy.ops.object.select_all(action='DESELECT')
 for ob in objects:ob.select_set(True)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Natf';neutral(rig)
 for act in list(bpy.data.actions):
  if act.name not in roles:bpy.data.actions.remove(act)
 for ob in bpy.data.objects:ob.select_set(ob in [rig,body])
 bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.gltf(filepath=str(out/f'mm6_natf_raw_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 print('EXPORTED',level,counts,flush=True)
(out/'export_info.json').write_text(json.dumps(info,indent=2));print('EXPORT_INFO',json.dumps(info),flush=True)
