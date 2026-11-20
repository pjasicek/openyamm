"""Local scene access and measured review views; posing uses the existing flyer helper."""
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bat_claude/scripts'))
import posing

def coordinates(mesh):
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data=evaluated.to_mesh()
    out=np.array([tuple(evaluated.matrix_world@v.co) for v in data.vertices])
    evaluated.to_mesh_clear()
    return out

def render(name,view='quarter',scale=1.3,target=(0,-.05,.2),textured=False):
    sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
    sh=sc.display.shading;sh.light='STUDIO';sh.show_cavity=not textured;sh.show_shadows=False
    sh.show_backface_culling=False
    sh.color_type='TEXTURE' if textured else 'SINGLE';sh.single_color=(.65,.72,.66)
    sh.background_type='VIEWPORT';sh.background_color=(.14,.14,.14)
    sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.resolution_percentage=100
    cam=bpy.data.objects.get('ReviewCamera')
    if cam is None:
        cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam)
    cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam
    d=Vector({'front':(0,-1,.02),'side':(1,0,.02),'quarter':(1,-1,.4),'back':(0,1,.1),'top':(0,0,1)}[view])
    cam.location=Vector(target)+d.normalized()*4
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(P/('review/'+name+'.png'));bpy.ops.render.render(write_still=True)
