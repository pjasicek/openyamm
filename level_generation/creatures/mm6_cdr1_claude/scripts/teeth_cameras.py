import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'));rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];out={}
ids={i for f in o.data.polygons if o.data.attributes['tooth_id'].data[f.index].value>0 for i in f.vertices}
for clip,frame in [('Standing',0),('Attack',8),('Attack',16)]:
 rig.animation_data.action=bpy.data.actions[clip];bpy.context.scene.frame_set(frame);e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();c=sum((me.vertices[i].co for i in ids),Vector())/len(ids);e.to_mesh_clear();out[clip+str(frame)]=[c.x,c.z,-c.y]
(P/'review/teeth_v2/cameras.json').write_text(json.dumps(out));print('CAMERAS',out)
