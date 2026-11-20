import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'detail_rebuild_01';OUT.mkdir(exist_ok=True)
source=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2']
s=bpy.data.scenes.new('Goblin - Complete Low Mesh Detail Test');bpy.context.window.scene=s
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.world=source.world;s.view_settings.view_transform='AgX';s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
for o in source.objects:
 if o.type in {'CAMERA','LIGHT'}:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp

def copy(o,name):
 cp=o.copy();cp.data=o.data.copy();cp.name=name;s.collection.objects.link(cp);cp.hide_viewport=False;cp.hide_render=False;cp.hide_set(False)
 return cp
body=copy(source.objects['Goblin_Body_WithFittedWaist'],'Goblin_Low_Body')
pouch=copy(source.objects['Goblin_PreservedPouch'],'Goblin_Low_Pouch')
skirt=copy(next(o for o in source.objects if o.name.startswith('Goblin_SkirtBelt_Low')),'Goblin_Low_SkirtBelt')
plates=[copy(o,'Goblin_Low_BackPlate_'+('L' if 'plate L' in o.name else 'R')) for o in source.objects if o.type=='MESH' and 'Upper-back plate' in o.name]
low=[body,pouch,skirt]+plates
report={'stage':'static low geometry and baked normal test; not rigged','meshes':[],'operations':[]}
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def tris(o):return sum(len(p.vertices)-2 for p in o.data.polygons)
def reduce(o,n):
 active(o);m=o.modifiers.new('Collapse to review budget','DECIMATE');m.ratio=n/tris(o);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)

def build():
 try:
  bpy.context.window.scene=s
  # The old spatial pouch cut also included a disconnected slice of the right hand.
  bm=bmesh.new();bm.from_mesh(pouch.data);todo=set(bm.verts);remove=[];components=[]
  while todo:
   first=todo.pop();stack=[first];component=[first]
   while stack:
    v=stack.pop()
    for e in v.link_edges:
     other=e.other_vert(v)
     if other in todo:todo.remove(other);stack.append(other);component.append(other)
   center=sum((v.co for v in component),Vector())/len(component);components.append({'verts':len(component),'center':list(center)})
   if center.x<-.34:remove.extend(component)
  bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(pouch.data);bm.free()
  report['pouch_input_components']=components;report['pouch_clean_triangles']=tris(pouch)
  # Remove small relief inside the central gorget. The rim and shoulder spikes stay outside the mask.
  active(body);group=body.vertex_groups.new(name='Gorget shallow relief only')
  for v in body.data.vertices:
   x,y,z=v.co;ax=abs(x)
   if y<-.065 and .42<z<.575 and ax<.145:
    w=min(1.,(.145-ax)/.035,(z-.42)/.035,(.575-z)/.025,(-.065-y)/.02)
    if w>0:group.add([v.index],w,'REPLACE')
  m=body.modifiers.new('Soften shallow central plate bumps','SMOOTH');m.factor=.8;m.iterations=24;m.vertex_group=group.name;bpy.ops.object.modifier_apply(modifier=m.name)
  report['operations'].append('Localized relief smoothing on interior of gorget only; no smoothing of spikes or mouth.')
  reduce(body,7800);reduce(pouch,320)
  for o in [body,pouch]+plates:
   active(o)
   # Bake and export use identical triangles and smooth normals.
   m=o.modifiers.new('Freeze bake triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=m.name)
   for p in o.data.polygons:p.use_smooth=True
   if not o.data.uv_layers:o.data.uv_layers.new(name='DetailBakeUV')
   bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
  for o in low:report['meshes'].append({'name':o.name,'triangles':tris(o)})
  report['triangles']=sum(tris(o) for o in low);report['operations'].append('Twelve separate back rivets (1200 triangles) omitted from low geometry; retained for plate normal bake.')
  (OUT/'build_report.json').write_text(json.dumps(report,indent=2))
  cam=s.camera;cam.location=(0,-4,0);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.15;s.render.filepath=str(OUT/'low_unbaked_front.png');bpy.ops.render.render(write_still=True)
  cam.location=(0,-4,.79);cam.rotation_euler=(Vector((0,0,.79))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.47;s.render.filepath=str(OUT/'low_unbaked_face.png');bpy.ops.render.render(write_still=True)
  (OUT/'build_done.txt').write_text('complete')
 except Exception:(OUT/'build_error.txt').write_text(traceback.format_exc())
 return None
bpy.app.timers.register(build,first_interval=.1)
print('Building complete low mesh in isolated scene.')
