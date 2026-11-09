import bpy,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/selected_lod0.blend'));o=bpy.data.objects['Body'];print('POLYGONS',len(o.data.polygons),max(len(f.vertices)for f in o.data.polygons),flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_mer1_portable_a.glb'));s=bpy.context.scene;r=next(o for o in bpy.data.objects if o.type=='ARMATURE');print('NLA',[(t.name,t.mute,t.is_solo,[(s.name,s.blend_type,s.influence)for s in t.strips])for t in r.animation_data.nla_tracks],flush=True)
from mathutils import Vector
for role,t,px,py in [('Attack',.4,110,545),('Death',1.3,446,655)]:
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==role);r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=t*s.render.fps/s.render.fps_base;s.frame_set(int(f),subframe=f%1);center=sum((r.matrix_world@r.pose.bones[f'B_{sd}_UpperArm'].head for sd in 'LR'),Vector())*.5
 origin=center+Vector(((px/800-.5)*.9,-6,(.5-py/800)*.9));hit,loc,n,idx,obj,mat=s.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,Vector((0,1,0)));face=obj.data.polygons[idx];print('HIT',role,idx,obj.name,'material',obj.data.materials[face.material_index].name,flush=True)
 for vi in face.vertices:
  v=obj.data.vertices[vi];print('VERT',vi,list(v.co),[(obj.vertex_groups[g.group].name,g.weight)for g in v.groups],flush=True)
