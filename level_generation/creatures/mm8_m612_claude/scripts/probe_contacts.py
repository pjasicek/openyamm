import bpy,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
report=json.loads((P/'work/contacts.json').read_text())
out=P/'review/contact_findings';out.mkdir(exist_ok=True)
common.workbench_clay(sc)
for clip,findings in report.items():
 for part,item in findings.items():
  a=bpy.data.actions[clip];rig.animation_data.action=a
  if a.slots:rig.animation_data.action_slot=a.slots[0]
  f=item['frame'];sc.frame_set(int(f),subframe=f-int(f))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  pos=me.vertices[item['vertex']].co.copy()
  face=[me.vertices[i].co.copy() for i in item['face']]
  ev.to_mesh_clear()
  print('FINDING',clip,part,'point',list(pos),'face',[list(v) for v in face],flush=True)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.012,location=pos)
  marker=bpy.context.object;mat=bpy.data.materials.new('Contact red');mat.diffuse_color=(1,0,0,1);marker.data.materials.append(mat)
  common.render_views(str(out/f'{clip}_{part}'),1.0,2.2,views=('front','left','three_quarter'),resolution=(440,440))
  bpy.data.objects.remove(marker,do_unlink=True)
