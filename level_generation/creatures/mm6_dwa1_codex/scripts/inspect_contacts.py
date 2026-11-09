import bpy,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];scene=bpy.context.scene;common.workbench_clay(scene)
for name,f,i in [('Attack',18.75,2335),('Death',8.75,2278),('Running',4.375,2305),('Fidget',20,2109)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(int(f),subframe=f-int(f));ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=ob.matrix_world@m.vertices[i].co;ev.to_mesh_clear();print('HEADPOINT',name,i,list(ob.data.vertices[i].co),list(co))
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.009,location=co);sp=bpy.context.object;mat=bpy.data.materials.new('bad');mat.diffuse_color=(1,.02,.02,1);sp.data.materials.append(mat)
 common.render_views(str(P/f'review/contact_{name}'),co.z,.68,views=('front','left','three_quarter'),target=(co.x,co.y),resolution=(500,500));bpy.data.objects.remove(sp,do_unlink=True)
