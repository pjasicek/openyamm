"""Identify the cuirass on the retained UV mesh; sleeves stay deformable."""
import numpy as np
from pathlib import Path
import bpy

def armour_mask(body):
    me=body.data;co=np.array([tuple(v.co) for v in me.vertices]);piece=np.array([a.value for a in me.attributes['piece'].data])
    image=bpy.data.images.load(str(Path(__file__).resolve().parents[1]/'textures/necromancer_basecolor_1k.png'),check_existing=True)
    pixels=np.array(image.pixels[:]).reshape(image.size[1],image.size[0],4);uv=me.uv_layers['UVMap'].data
    rgb=np.zeros((len(co),3));counts=np.zeros(len(co))
    for face in me.polygons:
        for vi,li in zip(face.vertices,face.loop_indices):
            u,v=uv[li].uv;x=int(np.clip(u*image.size[0],0,image.size[0]-1));y=int(np.clip(v*image.size[1],0,image.size[1]-1))
            rgb[vi]+=pixels[y,x,:3];counts[vi]+=1
    rgb/=np.maximum(counts,1)[:,None];bright=rgb.max(1);saturation=(bright-rgb.min(1))/np.maximum(bright,1e-6)
    width=np.interp(co[:,2],[1.06,1.34,1.42,1.48],[.19,.19,.225,.16])
    envelope=(piece==0)&(co[:,2]>1.065)&(co[:,2]<1.48)&(abs(co[:,0])<width)
    metal=envelope&(bright>.16)&(saturation<.30)
    # Include dark metal creases enclosed by the rigid plate, keeping the cloth seams outside.
    core=envelope&(abs(co[:,0])<.15)&(co[:,2]>1.10)&(co[:,2]<1.39)
    return metal|core,co,piece

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path(__file__).parent));import common
    p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
    body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis.identity()
    mask,co,piece=armour_mask(body);body.data.materials.clear()
    for name,color in [('Cloth',(.12,.16,.2,1)),('Rigid armour',(.9,.25,.05,1)),('Cord',(.15,.8,.3,1))]:
        mat=bpy.data.materials.new(name);mat.diffuse_color=color;body.data.materials.append(mat)
    for f in body.data.polygons:f.material_index=2 if all(piece[i] in (5,6,7) for i in f.vertices) else int(any(mask[i] for i in f.vertices))
    for o in bpy.data.objects:
        if o.type=='MESH':o.hide_render=o!=body
    common.workbench_clay(bpy.context.scene)
    common.render_views(str(p/'review/armour_fix/mask'),1.2,.75,views=('front','back','left'),resolution=(900,900))
    print('ARMOUR VERTICES',int(mask.sum()))
