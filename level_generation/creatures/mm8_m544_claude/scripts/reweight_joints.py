"""Smooth the proximal leg transition while preserving rigid hooves, face, mesh and UVs."""
from pathlib import Path
import bpy
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
mesh=bpy.data.objects['Unicorn'];rig=bpy.data.objects['Unicorn_Rig']
rig.animation_data.action=None
for bone in rig.pose.bones:bone.matrix_basis.identity()
groups=list(mesh.vertex_groups)
w=np.zeros((len(mesh.data.vertices),len(groups)))
for v in mesh.data.vertices:
    for g in v.groups:w[v.index,g.group]=g.weight
names=[g.name for g in groups]
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for v in mesh.data.vertices:
    x,y,z=v.co
    side='L' if x>0 else 'R'
    proximal=('UpperArm_'+side if y<-.10 else 'Thigh_'+side if .045<y<.3 else None)
    if proximal and z>.28:
        limb=[i for i,n in enumerate(names) if n.endswith('_'+side) and
              n.startswith(('UpperArm','ForeArm','FrontPastern','FrontHoof') if y<0 else ('Thigh','Shin','HindPastern','HindHoof'))]
        mass=w[v.index,limb].sum()
        w[v.index,limb]=0;w[v.index,names.index(proximal)]=mass
neighbors=[[] for v in mesh.data.vertices]
for e in mesh.data.edges:
    a,b=e.vertices;neighbors[a].append(b);neighbors[b].append(a)
for step in range(8):
    new=w.copy()
    for v in mesh.data.vertices:
        x,y,z=v.co
        if .18<z<.46 and -.30<y<.295:
            strength=.55*smooth(.18,.25,z)*(1-smooth(.40,.46,z))
            new[v.index]=(1-strength)*w[v.index]+strength*w[neighbors[v.index]].mean(axis=0)
    w=new
for g in groups:g.remove(list(range(len(w))))
for v in mesh.data.vertices:
    ids=np.argsort(w[v.index])[-4:];total=w[v.index,ids].sum()
    for i in ids:
        value=w[v.index,i]/total
        if value>1e-7:groups[i].add([v.index],float(value),'REPLACE')
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 and len(v.groups)<=4 for v in mesh.data.vertices)
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/uv_reweighted.blend'))
