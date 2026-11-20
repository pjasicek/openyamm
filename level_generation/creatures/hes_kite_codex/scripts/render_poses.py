"""Render named frames from an owned master, using CPU Cycles without a desktop."""
import bpy,json,math,os,sys,traceback
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
try:
    blend,destination,spec=sys.argv[sys.argv.index('--')+1:]
    bpy.ops.wm.open_mainfile(filepath=str(P/blend))
    rig=bpy.data.objects['Ashkite_Rig'];sc=bpy.context.scene
    out=P/destination;out.mkdir(parents=True,exist_ok=True)
    sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
    sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.resolution_percentage=100
    sc.view_settings.view_transform='AgX';sc.render.image_settings.file_format='PNG'
    sc.world=bpy.data.worlds.new('Review world');sc.world.color=(.18,.18,.18)
    bpy.ops.mesh.primitive_plane_add(size=12,location=(0,0,-.006));floor=bpy.context.object;floor.name='ReviewFloor'
    fm=bpy.data.materials.new('Floor');fm.use_nodes=True;fm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.10,.11,.12,1);fm.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.95;floor.data.materials.append(fm)
    for i,xyz in enumerate([(2,-3,4),(-3,-2,2),(0,4,3)]):
        d=bpy.data.lights.new('Light'+str(i),'AREA');d.energy=450;d.size=4
        ob=bpy.data.objects.new(d.name,d);sc.collection.objects.link(ob);ob.location=xyz
        ob.rotation_euler=(Vector((0,0,.6))-ob.location).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera');cd.type='ORTHO';cd.ortho_scale=4.1
    cam=bpy.data.objects.new('Camera',cd);sc.collection.objects.link(cam);sc.camera=cam
    views={'quarter':((3,-4,2.5),(0,0,.65)), 'front':((0,-5,.8),(0,0,.7)),
           'side':((5,0,.8),(0,0,.7)), 'head':((1.2,-2,1.28),(0,-.72,.88)), 'top':((0,0,5),(0,0,0)), 'feet':((2,-3,.85),(0,-.02,.52))}
    for entry in json.loads(spec):
        clip,frame,view=entry;rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame)
        loc,tgt=views[view];cd.ortho_scale={'head':1.1,'feet':1.2}.get(view,4.1);cam.location=loc;cam.rotation_euler=(Vector(tgt)-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(out/f'{clip}_{frame:03d}_{view}.png');bpy.ops.render.render(write_still=True)
        assert Path(sc.render.filepath).exists()
    print('Rendered',len(json.loads(spec)),'poses',flush=True)
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
