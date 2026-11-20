from pathlib import Path
import bpy,json
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
def add_club(rig):
 with bpy.data.libraries.load(str(P/'work/club_clean.blend'),link=False) as (src,dst):dst.objects=['ClubMesh']
 obj=dst.objects[0];bpy.context.scene.collection.objects.link(obj)
 g=json.loads((P/'work/grip_pose.json').read_text());c=Vector(g['handle_centre_hand_local']);axis=Vector(g['handle_axis_hand_local']).normalized()
 rotation=Vector((0,0,1)).rotation_difference(axis)
 for v in obj.data.vertices:v.co=c+rotation@v.co
 obj.matrix_world=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix
 return obj
