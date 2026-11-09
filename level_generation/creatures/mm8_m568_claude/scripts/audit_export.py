"""Delivered geometry parity and half-frame floor, grip and weapon/torso checks."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];FPS=48
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m568.blend'));sc=bpy.context.scene
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];weapon=bpy.data.objects['PolearmMesh']
G=json.loads((P/'work/grip_pose.json').read_text());dur=json.loads((P/'work/animation_audit.json').read_text())
def co(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();a=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return a
def at(t,offset=1):
 f=t*FPS+offset;sc.frame_set(int(f),subframe=f%1)
refs={};report={};names={g.index:g.name for g in body.vertex_groups}
dominant=[names[max(v.groups,key=lambda g:g.weight).group] for v in body.data.vertices]
main=lambda n:n.startswith('Serpent_') or n in ['Root','B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']
torso=[tuple(f.vertices) for f in body.data.polygons if all(main(dominant[i]) for i in f.vertices)]
propfaces=[tuple(f.vertices) for f in weapon.data.polygons]
handfaces=[tuple(f.vertices) for f in body.data.polygons if all('Finger' in dominant[i] or dominant[i].endswith('_Hand') for i in f.vertices)]
for role,meta in dur.items():
 rig.animation_data.action=bpy.data.actions[role];refs[role]=[];minimum=10.;grip=0.;contacts=[];hand_contacts=[]
 for frac in [0,.2,.4,.6,.8,1]:
  at(frac*meta['duration']);refs[role].append((frac,co(body)+co(weapon),list(bpy.data.objects['Socket_Polearm_Tip'].matrix_world.translation)))
 for sample in range(round(meta['duration']*FPS*2)+1):
  t=sample/(FPS*2);at(t);bc=co(body);wc=co(weapon);minimum=min(minimum,min(v.z for v in bc),min(v.z for v in wc))
  deformation=rig.pose.bones['Polearm'].matrix@rig.data.bones['Polearm'].matrix_local.inverted();center=deformation@Vector((0,0,0));axis=deformation.to_3x3()@Vector((0,0,1))
  for side in ['L','R']:
   if (role=='Fidget' and side=='L') or role in ['Death','Dead']:continue
   contact=rig.pose.bones['B_'+side+'_Hand'].matrix@Vector(G[side]['handle_centre_hand_local']);expected=center+axis*(.25 if side=='R' else -.25);grip=max(grip,(contact-expected).length)
  torso_tree=BVHTree.FromPolygons(bc,torso);overlaps=torso_tree.overlap(BVHTree.FromPolygons(wc,propfaces))
  h=torso_tree.overlap(BVHTree.FromPolygons(bc,handfaces))
  if h:hand_contacts.append({'time':t,'pairs':len(h)})
  if overlaps:
   vertices={i for a,b in overlaps for i in torso[a]};center=np.mean([bc[i] for i in vertices],axis=0);contacts.append({'time':t,'pairs':len(overlaps),'center':center.tolist(),'bones':sorted({dominant[i] for i in vertices})})
 report[role]={'samples':sample+1,'minimum_z_m':minimum,'held_grip_error_m':grip,'weapon_torso_intersections':contacts,'hand_torso_intersections':hand_contacts}
 assert not contacts and not hand_contacts,(role,'body intersections',contacts,hand_contacts)
 assert minimum>-.015,(role,'floor',minimum)
 assert grip<.008,(role,'grip',grip)
 print(role,report[role],flush=True)
(P/'review/checks/dense_contacts.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m568_lod0.glb'));sc=bpy.context.scene;sc.render.fps=FPS
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH')
for role,frames in refs.items():
 action=next(a for a in bpy.data.actions if a.name==role or a.name.endswith('|'+role));rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];err=0.;sock=0.
 for frac,expected,tip in frames:
  lo,hi=action.frame_range;f=lo+frac*(hi-lo);sc.frame_set(int(f),subframe=f%1);actual=co(body);tree=KDTree(len(actual))
  for i,v in enumerate(actual):tree.insert(v,i)
  tree.balance();err=max(err,max(tree.find(v)[2] for v in expected));sock=max(sock,(bpy.data.objects['Socket_Polearm_Tip'].matrix_world.translation-Vector(tip)).length)
 assert err<.0001 and sock<.0001,(role,'parity',err,sock)
 report[role].update(export_surface_error_m=err,export_socket_error_m=sock)
(P/'review/checks/export_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('EXPORT PARITY PASS',flush=True)
