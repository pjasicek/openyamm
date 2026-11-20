"""Protected, measured reduction candidates. Geometry only; accepted action samples are never authored here."""
import bpy,bmesh,sys,json,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
OUT=P/'review/round4';WORK=P/'work/round4';WORK.mkdir(exist_ok=True)
CALIBRATION={}
ROLES=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']

def activate(name,time=0):
 rig=bpy.data.objects['Rig'];a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=time*bpy.context.scene.render.fps;bpy.context.scene.frame_set(int(f),subframe=f%1)
def reset():
 rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
def triangles(o):return sum(len(f.vertices)-2 for f in o.data.polygons)
def cleanup():
 for o in list(bpy.data.objects):
  if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
def protect(obj,kind):
 reset();me=obj.data
 # Keep exported UV splits as topology boundaries so collapse cannot interpolate across unrelated charts.
 me.update()
 co=np.array([tuple(obj.matrix_world@v.co)for v in me.vertices]);names={g.index:g.name for g in obj.vertex_groups};protected=np.zeros(len(co),bool);reasons={}
 if kind=='body':
  pv=np.array([x.value for x in me.attributes['piece'].data]);face=(pv==0)&(co[:,1]<.025)&(co[:,2]>.965)
  hands=np.array([sum(g.weight for g in v.groups if 'Hand'in names[g.group]or 'Finger'in names[g.group])>.1 for v in me.vertices]);soles=co[:,2]<.016
  loops=np.zeros(len(co),bool)
  for sd in 'LR':
   for n,radius in [('UpperArm',.065),('Forearm',.042),('Thigh',.065),('Calf',.04)]:
    J=np.array(bpy.data.objects['Rig'].data.bones[f'B_{sd}_{n}'].head_local);loops|=np.linalg.norm(co-J,axis=1)<radius
  for label,m in [('face',face),('hands_fingers_grip',hands),('deformation_loops',loops),('sole_contact',soles)]:protected|=m;reasons[label]=int(m.sum())
 else:
  # The wrist-fixed grip surface is never simplified; rim/silhouette protection below retains the cutting profile.
  hand=bpy.data.objects['Rig'].data.bones['B_R_Hand'].head_local;m=np.linalg.norm(co-np.array(hand),axis=1)<.065;protected|=m;reasons['grip_contact']=int(m.sum())
 # Detect visible contours on a welded analysis copy, keeping UV splits intact in the actual mesh.
 from mathutils.bvhtree import BVHTree
 from mathutils.kdtree import KDTree
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.verts.ensure_lookup_table();bm.normal_update();bm.verts.index_update()
 tree=BVHTree.FromBMesh(bm);contour=[]
 dirs=[Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),0))for i in range(8)]
 for e in bm.edges:
  midpoint=(e.verts[0].co+e.verts[1].co)*.5
  for direction in dirs:
   if len(e.link_faces)==2 and e.link_faces[0].normal.dot(direction)*e.link_faces[1].normal.dot(direction)>=-1e-7:continue
   hit=tree.ray_cast(midpoint+direction*10,-direction,10.002)
   if hit[0] is None or abs(hit[3]-10)<.001:
    contour.extend(v.co.copy()for v in e.verts);break
 kd=KDTree(len(contour))
 for i,v in enumerate(contour):kd.insert(v,i)
 kd.balance();edge_mask=np.array([kd.find(v.co)[2]<1e-6 for v in me.vertices]);protected|=edge_mask;reasons['eight_view_visible_contours']=int(edge_mask.sum());bm.free()
 group=obj.vertex_groups.get('_reduction_protect')or obj.vertex_groups.new(name='_reduction_protect');group.add(np.flatnonzero(protected).tolist(),1,'REPLACE');reasons['total']=int(protected.sum());reasons['vertices']=len(co)
 return reasons

def reduce(obj,ratio,planar=False):
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 if planar:
  bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();di=bm.verts.layers.deform.active;gi=obj.vertex_groups['_reduction_protect'].index
  allowed={v for v in bm.verts if v[di].get(gi,0)<.5};edges=[e for e in bm.edges if all(v in allowed for v in e.verts)]
  bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(.25),use_dissolve_boundaries=False,verts=list(allowed),edges=edges,delimit={'NORMAL','MATERIAL','SEAM','SHARP','UV'});bm.to_mesh(obj.data);bm.free()
 mod=obj.modifiers.new('MeasuredCollapse','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=ratio;mod.use_collapse_triangulate=True;mod.vertex_group='_reduction_protect';mod.invert_vertex_group=True;mod.vertex_group_factor=1000
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
 # Remove simplification weights from normalization; only actual deform joints belong to the skin.
 gi=obj.vertex_groups['_reduction_protect'].index
 for v in obj.data.vertices:
  weights=[(g.group,g.weight)for g in v.groups if g.group!=gi];weights=sorted(weights,key=lambda t:-t[1])[:8];total=sum(w for _,w in weights);assert total>0
  for g in list(v.groups):
   if g.group!=gi:obj.vertex_groups[g.group].remove([v.index])
  for g,w in weights:obj.vertex_groups[g].add([v.index],w/total,'REPLACE')

def render(dest,kind,level):
 dest.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene;common.workbench_clay(scene,True);scene.render.film_transparent=True;scene.display.render_aa='16';scene.render.resolution_x=820;scene.render.resolution_y=820;scene.render.resolution_percentage=100
 for mat in bpy.data.materials:
  if mat.node_tree:
   bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 body=bpy.data.objects['Body'];axe=bpy.data.objects['Axe'];body.hide_render=kind!='body';axe.hide_render=kind!='axe'
 # Body matches viewer FOV/820px viewport/4.3m orbit. Lower levels use exact engine projected-bound thresholds.
 diameter=CALIBRATION.setdefault('diameter',float(np.linalg.norm(np.ptp(np.array([tuple(body.matrix_world@v.co)for v in body.data.vertices]),axis=0))));focal=820/(2*math.tan(math.radians(35)/2));distance=4.3 if level==0 else focal*diameter/[0,500,200,80][level]+diameter/2
 poses=[('Standing',0),('Running',.12),('Attack',.71875),('Death',.6)] if kind=='body'else [('Standing',0)]
 for role,t in poses:
  activate(role,t)
  if kind=='axe':
   ev=axe.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([tuple(axe.matrix_world@v.co)for v in mesh.vertices]);ev.to_mesh_clear();target=Vector(CALIBRATION.setdefault('axe_center',((co.min(0)+co.max(0))/2).tolist()));dist=1.8 if level==0 else distance
  else:target=Vector((0,0,1.0));dist=distance
  for i in range(8):
   angle=i*math.pi/4;camdata=bpy.data.cameras.new('Reduction camera');camdata.lens_unit='FOV';camdata.angle=math.radians(35);cam=bpy.data.objects.new('Reduction camera',camdata);scene.collection.objects.link(cam);cam.location=target+Vector((math.sin(angle),-math.cos(angle),0))*dist;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.filepath=str(dest/f'{role}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 body.hide_render=False;axe.hide_render=False
 return {'distance_m':distance,'viewport_px':820,'fov_degrees':35,'bound_diameter_m':diameter,'switch_pixels':[None,500,200,80][level]}

def evaluate(ref,folder):
 r=subprocess.run(['/usr/bin/python3',str(P/'scripts/round4_image_metrics.py'),str(ref),str(folder)],check=True,capture_output=True,text=True);return json.loads(r.stdout)

def search(config):
 CALIBRATION.clear();CALIBRATION['diameter']=json.loads((OUT/'body_lod0_curve.json').read_text())['camera']['bound_diameter_m'];kind=config.get('kind','body');level=config.get('level',0);maxsteps=config.get('steps',1);tag=f'{kind}_lod{level}'
 source=WORK/f'accepted_lod{level}.blend'if config.get('accepted_level')else P/'work/round4_before/work/export_reimport.blend'
 bpy.ops.wm.open_mainfile(filepath=str(source));cleanup();reset();obj=bpy.data.objects['Body'if kind=='body'else 'Axe'];before=triangles(obj)
 ref=OUT/tag/'reference';camera=render(ref,kind,level);protection=protect(obj,kind);baseline=WORK/f'{tag}_0.blend';bpy.ops.wm.save_as_mainfile(filepath=str(baseline));curve=[]
 for step in range(1,maxsteps+1):
  bpy.ops.wm.open_mainfile(filepath=str(WORK/f'{tag}_{step-1}.blend'));reset();obj=bpy.data.objects['Body'if kind=='body'else 'Axe'];reduce(obj,.9,planar=step==1);count=triangles(obj);path=WORK/f'{tag}_{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));folder=OUT/tag/f'step_{step:02}';render(folder,kind,level);metrics=evaluate(ref,folder)
  row={'step':step,'triangles':count,'ratio_to_original':count/before,'visual':metrics,'blend':str(path.relative_to(P))};curve.append(row);(OUT/f'{tag}_curve.json').write_text(json.dumps({'kind':kind,'level':level,'before':before,'reference':str(source.relative_to(P)),'camera':camera,'protection':protection,'steps':curve},indent=2)+'\n');print('REDUCTION',tag,step,count,metrics['min_iou'],metrics['min_ssim'],metrics['pass'],flush=True)
  if not metrics['pass'] or (step>1 and count==curve[-2]['triangles']):break

if __name__=='__main__':
 config=json.loads((WORK/'config.json').read_text())
 for job in config.get('jobs',[config]):search(job)
