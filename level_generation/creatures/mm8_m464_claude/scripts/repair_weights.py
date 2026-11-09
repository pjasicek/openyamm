"""Remove source-transfer weight discontinuities on clothing; align new boot soles to the accepted gait."""
import bpy,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
# Replace only actions from the revised pose checkpoint; UVs and texture ownership remain authoritative here.
r.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/animated_master.blend'),link=False)as(src,dst):dst.actions=src.actions
for a in dst.actions:a.use_fake_user=True
co=np.array([v.co[:]for v in me.vertices]);part=np.array([x.value for x in me.attributes['part'].data]);names=[g.name for g in body.vertex_groups];w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
# Spatial smoothing over the jacket fixes nearest-source-triangle discontinuities at the axilla.
ids=np.flatnonzero(part==2);tree=kdtree.KDTree(len(ids))
for i in ids:tree.insert(Vector(co[i]),int(i))
tree.balance();smooth=w.copy()
for i in ids:
 if co[i,2]<.94:continue
 near=tree.find_range(Vector(co[i]),.09);nn=np.array([j for _,j,_ in near]);d=np.array([dd for _,_,dd in near]);a=np.exp(-.5*(d/.035)**2);smooth[i]=(w[nn]*a[:,None]).sum(0)/a.sum()
for i in ids:
 order=np.argsort(smooth[i])[-4:];row=np.zeros(len(names));row[order]=smooth[i,order];row/=row.sum()
 for g in body.vertex_groups:g.remove([int(i)])
 for j in np.flatnonzero(row>1e-7):body.vertex_groups[int(j)].add([int(i)],float(row[j]),'REPLACE')
sys.path.insert(0,str(P/'scripts'))
from fit_sleeves import fit_sleeves
fit_sleeves(body,r,P)
for v in me.vertices:
 if part[v.index]!=0 or v.co.z>.25:continue
 side='L'if v.co.x>0 else'R';ankle=r.data.bones[f'B_{side}_Foot'].head_local;blend=max(0,min(1,(.25-v.co.z)/.10));angle=math.radians(-8 if side=='L'else 12)*blend;v.co=ankle+Matrix.Rotation(angle,3,'Z')@(v.co-ankle);v.co.z+=.002*max(0,min(1,(.15-v.co.z)/.07))
for mat in me.materials:mat.use_backface_culling=True
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/repaired_master.blend'))
