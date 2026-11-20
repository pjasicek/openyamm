import bpy,sys,numpy as np,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/body_lod0_4_final.blend'));C.activate('Death',1.1041666667);o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();point=me.vertices[4258].co.copy();ev.to_mesh_clear();bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.008,location=point);mark=bpy.context.object;mat=bpy.data.materials.new('Gate sample');mat.diffuse_color=(1,0,0,1);mark.data.materials.append(mat);common.workbench_clay(bpy.context.scene,True);lo,hi=common.world_bounds([o,bpy.data.objects['ClubMesh']]);mid=(lo+hi)*.5;common.render_views(str(P/'review/hem_opening_Death'),mid.z,2.6,views=('front','left','three_quarter'),resolution=(800,800),target=(mid.x,mid.y))
