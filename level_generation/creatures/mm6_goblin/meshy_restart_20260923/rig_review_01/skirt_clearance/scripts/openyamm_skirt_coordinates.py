import bpy,json
from pathlib import Path
from mathutils import Vector
p=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01/skirt_clearance/strips.json');strips=json.loads(p.read_text());s=bpy.data.scenes['Goblin - Skirt Clearance v3'];bpy.context.window.scene=s;arm=s.objects['Goblin_SkirtClearance_Rig'];mesh=s.objects['Goblin_SkirtClearance_10577'];bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for x in strips:
 co=[mesh.matrix_world@mesh.data.vertices[i].co for i in x['ids']];zmax=max(v.z for v in co);top=[v for v in co if v.z>zmax-.017];pivot=sum(top,Vector())/len(top);radial=Vector((pivot.x,pivot.y-.035,0)).normalized();x['pivot']=list(pivot);x['radial']=list(radial);x['axis']=[radial.y,-radial.x,0];b=arm.data.edit_bones[x['name']];b.head=pivot;b.tail=pivot+Vector((0,0,-.15))
bpy.ops.object.mode_set(mode='OBJECT');p.write_text(json.dumps(strips,indent=2));print('Strip pivots in skeleton coordinates')
