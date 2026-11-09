"""Fit only lower-LOD grip radius against all animated finger surfaces."""
import bpy,json,sys,math,numpy as np,subprocess
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
selection=json.loads((P/'review/rebake/final_selection.json').read_text());reports={}
for level in [2,3]:
 tag=selection[str(level)]['tag'];path=P/f'work/rebake/{tag}_baked.blend';bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];W=np.zeros((len(me.vertices),len(names)))
 for v in me.vertices:
  for g in v.groups:W[v.index,g.group]=g.weight
 inv=rig.data.bones['Bow'].matrix_local.inverted();local=np.array([tuple(inv@v.co)for v in me.vertices]);faces=[list(f.vertices)for f in me.polygons if all(pv[i]==201 and abs(local[i,2])<.1 for i in f.vertices)];me.calc_loop_triangles();tris={}
 for digit in [0,1,2,4]:
  mask=W[:,[i for i,n in enumerate(names)if n.startswith(f'B_L_Finger{digit}')]].sum(1)>.4;tris[digit]=np.array([tuple(f.vertices)for f in me.loop_triangles if any(mask[i]for i in f.vertices)and all(pv[i]==3 for i in f.vertices)],dtype=int).reshape(-1,3)
 bary=np.array([[i,j,4-i-j]for i in range(5)for j in range(5-i)])/4;samples=[]
 for a in bpy.data.actions:
  rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
  for t in np.r_[np.arange(0,a.frame_range[1]/30,1/48),a.frame_range[1]/30]:
   f=t*30;bpy.context.scene.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();xyz=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear();inverse=np.array(rig.pose.bones['Bow'].matrix.inverted());xyz=(inverse@np.c_[xyz,np.ones(len(xyz))].T).T[:,:3]
   for digit,ids in tris.items():
    pts=np.einsum('jk,nkl->njl',bary,xyz[ids]).reshape(-1,3);pts=pts[abs(pts[:,2])<.110];assert len(pts);samples.append((a.name,float(t),digit,[Vector(p)for p in pts]))
 trials=[];chosen=None
 for scale in sorted(np.arange(.8,1.201,.01),key=lambda x:abs(x-1)):
  coords=local.copy();coords[:,:2]*=scale;tree=BVHTree.FromPolygons(coords.tolist(),faces);worst=(0,None,None,None)
  for role,t,digit,pts in samples:
   distance=min(tree.find_nearest(p)[3]for p in pts)
   if distance>worst[0]:worst=(distance,role,t,digit)
  trials.append({'scale':float(scale),'worst_m':worst[0],'clip':worst[1],'time':worst[2],'digit':worst[3]});print('GRIP_RADIUS',level,trials[-1],flush=True)
  if worst[0]<=.0029:chosen=float(scale);break
 assert chosen is not None,trials
 for v in me.vertices:
  if pv[v.index]!=201:continue
  p=Vector(local[v.index]);weight=max(0,min(1,(.14-abs(p.z))/.03));p.x*=1+(chosen-1)*weight;p.y*=1+(chosen-1)*weight;v.co=rig.data.bones['Bow'].matrix_local@p
 me.update();rig.animation_data.action=None
 for bone in rig.pose.bones:bone.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(path));reports[str(level)]={'chosen_radius_scale':chosen,'trials':trials,'geometry_change':'Grip radius only, full below 11 cm and tapered to zero at 14 cm from wrap center; UVs and rebaked maps retained.','triangles_unchanged':True}
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig;body.name=body.data.name='Lizard'
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
(P/'review/rebake/lower_grip_fit.json').write_text(json.dumps(reports,indent=2));subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_pack.py')],check=True)
print('LOWER_GRIPS_EXPORTED',flush=True)
