import bpy,bmesh,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
sc=bpy.context.scene;common.workbench_clay(sc);sc.display.shading.color_type='MATERIAL'
reports={}
for name in ['P00','P01']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
 edges={e for e in bm.edges if e.is_boundary};loops=[]
 while edges:
  seed=edges.pop();vs=set(seed.verts);todo=list(seed.verts)
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    if e in edges:
     edges.remove(e)
     for q in e.verts:
      if q not in vs:vs.add(q);todo.append(q)
  loops.append({'n':len(vs),'lo':[min(v.co[a] for v in vs) for a in range(3)],'hi':[max(v.co[a] for v in vs) for a in range(3)],'ids':[v.index for v in vs]})
 reports[name]=loops;bm.free()
(P/'review/boundaries.json').write_text(json.dumps(reports,indent=2))
def shot(name,loc,target,scale):
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.filepath=str(P/'review'/f'{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
shot('hands_front',(0.64,-3,.68),(.64,0,.68),.34)
shot('hands_side',(3,.1,.68),(.64,0,.68),.34)
shot('flank',(3,-3,1.15),(.2,0,1.15),.6)
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=o.name!='P01'
shot('pelvis',(0,-3,.84),(0,0,.84),.8)
print('BOUNDARIES',[(k,[(x['n'],x['lo'],x['hi']) for x in v]) for k,v in reports.items()])
