from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
b=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=b.data
me.materials.clear()
for name,job,uvname in [('Centaur','body_texture_v1','UVMap'),('CentaurHead','head_texture_v1','HeadUV')]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.78
    uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map=uvname
    tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(P/'meshy'/job/'texture_urls_0_base_color.png'));nt.links.new(uv.outputs['UV'],tx.inputs['Vector']);nt.links.new(tx.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
for p in me.polygons:p.material_index=me.attributes['head'].data[p.index].value
# Raster inputs preserve original topology and both UV layouts for texture class masks.
me.calc_loop_triangles();tri=list(me.loop_triangles)
np.savez_compressed(P/'work/uv3d.npz',vertices=np.array([v.co[:]for v in me.vertices]),faces=np.array([t.vertices[:]for t in tri]),head=np.array([me.attributes['head'].data[t.polygon_index].value for t in tri]),component=np.array([v.value for v in me.attributes['component'].data]),uv=np.array([[me.uv_layers['UVMap'].data[l].uv[:]for l in t.loops]for t in tri]),head_uv=np.array([[me.uv_layers['HeadUV'].data[l].uv[:]for l in t.loops]for t in tri]))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/preview_materials.blend'))
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True
sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.film_transparent=False
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.24,.28,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
sc.view_settings.view_transform='Standard';sc.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [x.identifier for x in sc.view_settings.bl_rna.properties['look'].enum_items]else'None'
for name,loc,power,size in [('Key',(-3,-4,6),600,5),('Fill',(4,-1,4),400,4),('Rim',(0,3,4),350,3)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,-.2,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
shots=[('Standing',0,'side'),('Standing',0,'grip'),('Attack',23,'side'),('Death',13,'side')]
for name,f,view in shots:
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(f)
    dg=bpy.context.evaluated_depsgraph_get();ev=b.evaluated_get(dg);m=ev.to_mesh();pts=np.array([v.co[:]for v in m.vertices]);ev.to_mesh_clear();c=Vector((pts.min(0)+pts.max(0))/2)
    direction={'front':(0,-1,.03),'side':(-1,0,.05),'quarter':(-.7,-1,.15),'grip':(1,-1,.25)}[view];cam.data.ortho_scale=3.6
    if view=='grip':c=rig.pose.bones['Bow'].head;cam.data.ortho_scale=.5
    cam.location=c+Vector(direction)*8;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(P/'review'/f'pose_{name}_{f}_{view}.png');bpy.ops.render.render(write_still=True)
