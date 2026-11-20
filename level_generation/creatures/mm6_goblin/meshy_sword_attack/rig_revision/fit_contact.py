"""Remove handle penetration from the posed pads and report each source digit's closest contact."""
import bpy,json,math
from mathutils import Vector
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack/rig_revision');s=bpy.data.scenes['Goblin Arm Rig Revision'];r=bpy.data.objects['Goblin Arm Revision Rig'];body=bpy.data.objects['Goblin Arm Revision Body'];key=body.data.shape_keys.key_blocks['SwordGrip'];basis=body.data.shape_keys.key_blocks['Basis'];inv=r.data.bones['mixamorig:RightHand'].matrix_local.inverted()@body.matrix_world;back_to_mesh=inv.inverted();W=Vector((.50113,0,-.86537)).normalized();B=W.cross(Vector((0,1,0)))
source_scene=bpy.data.scenes['Meshy Goblin Sword and Native Attack'];source=next(o for o in source_scene.objects if o.type=='MESH' and o.data.shape_keys);source_groups={g.index for g in source.vertex_groups if g.name in ['mixamorig:RightHand','mixamorig:RightHandMiddle4']}
contacts={i:[] for i in range(5)};changed=0
for old,orig,dest in zip(source.data.vertices,basis.data,key.data):
 if sum(g.weight for g in old.groups if g.group in source_groups)<.5:continue
 raw=inv@orig.co
 if raw.y<.12:continue
 raww=raw.dot(W);digit=0 if raww<-.081 else 1 if raww<-.058 else 2 if raww<-.02 else 3 if raww<.026 else 4
 p=inv@dest.co;w=p.dot(W);y=p.y-.102;n=p.dot(B)+.046;radius=math.hypot(y,n)
 if -.095<w<.070:
  if radius<.0266 and radius>1e-6:
   y*=.0266/radius;n*=.0266/radius;p=W*w+Vector((0,y+.102,0))+B*(n-.046);dest.co=back_to_mesh@p;changed+=1;radius=.0266
  contacts[digit].append(radius-.0266)
report={'corrected_vertices':changed,'closest_pad_clearance_by_source_digit':{str(k):min(v) if v else None for k,v in contacts.items()},'method':'radial clearance to handle incl. winding; digit bins inferred from original hand coordinates, not anatomical finger bones'}
(ROOT/'review/grip_contact.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
