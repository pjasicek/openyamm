import bpy,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/before_shoulder_field.blend'));C.reset();o=bpy.data.objects['Body'];pv=[v.value for v in o.data.attributes['piece'].data]
def smooth(t):t=float(np.clip(t,0,1));return t*t*(3-2*t)
for v in o.data.vertices:
 if pv[v.index]!=1:continue
 x,y,z=v.co;sd='L'if x>0 else'R';w={o.vertex_groups[g.group].name:g.weight for g in v.groups};t=smooth((z-1.07)/.13)
 for n in list(w):
  if n in ['B_Pelvis','B_Spine','B_Spine1','B_L_Clavicle','B_R_Clavicle']:
   move=w[n]*t;w[n]-=move;w['B_Spine2']=w.get('B_Spine2',0)+move
 if abs(x)<.29:
  keep=smooth((abs(x)-.12)/.16)
  for n in list(w):
   if 'UpperArm'in n:
    move=w[n]*(1-keep);w[n]-=move;w['B_Spine2']=w.get('B_Spine2',0)+move
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 ws=sorted(w.items(),key=lambda x:-x[1])[:4];total=sum(x for n,x in ws)
 for n,x in ws:
  if x>1e-8:o.vertex_groups[n].add([v.index],x/total,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master.blend'));common.workbench_clay(bpy.context.scene,True);bpy.context.scene.display.shading.show_specular_highlight=False
for role,t in [('Attack',.416667),('Attack',1.083333),('Death',1.3)]:
 C.activate(role,t);common.render_views(str(P/'review/round3'/f'shoulder_field_{role}_{t}'),1.15,1.2,views=('front','left','back'),resolution=(800,900))
