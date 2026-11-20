"""Area-weighted cloth texel density, UV aspect and albedo comparison on the selected master."""
import bpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mnk1.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();P=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear();C=np.array([v.co[:] for v in me.vertices]);piece=np.array([x.value for x in me.attributes['piece'].data]);tags=[x.value for x in me.attributes['cuff'].data];me.calc_loop_triangles();uv=me.uv_layers['UVMap'].data
im=bpy.data.images.load(str(p/'textures/mnk1_basecolor_2k.png'),check_existing=False);im.colorspace_settings.name='Non-Color';pixels=np.array(im.pixels[:]).reshape(2048,2048,4)[...,:3];L=np.array([.2126,.7152,.0722]);rows={'sleeves':[],'torso':[]}
for tri in me.loop_triangles:
 ids=list(tri.vertices);center=C[ids].mean(0);tag=tags[tri.polygon_index]
 kind='sleeves' if tag==1 else 'torso' if tag==0 and all(piece[i]==0 for i in ids) and abs(center[0])<.12 and 1.05<center[2]<1.35 else None
 if kind is None:continue
 V=P[ids];T=np.array([uv[i].uv[:] for i in tri.loops]);e1=V[1]-V[0];e2=V[2]-V[0];normal=np.cross(e1,e2);area=np.linalg.norm(normal)/2
 if area<1e-10:continue
 ex=e1/np.linalg.norm(e1);ey=np.cross(normal/np.linalg.norm(normal),ex);A=np.array([[e1@ex,e2@ex],[e1@ey,e2@ey]]);J=(T[1:]-T[0]).T*2048@np.linalg.inv(A);sv=np.linalg.svd(J,compute_uv=False)
 rgb=[]
 for a,z in [(1/3,1/3),(.2,.2),(.2,.6),(.6,.2),(.1,.1),(.1,.8),(.8,.1)]:
  q=T[0]*(1-a-z)+T[1]*a+T[2]*z;x,y=np.clip((q*2048).astype(int),0,2047);rgb.append(pixels[y,x])
 rgb=np.array(rgb);cloth=(rgb[:,2]>rgb[:,0]*1.45)&((rgb@L)>.04)&((rgb@L)<.4)
 if not cloth.any():continue
 rgb=rgb[cloth];linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
 rows[kind].append([area,float(np.sqrt(sv.prod())),float(sv.max()/max(sv.min(),1e-12)),float((rgb@L).mean()),float((linear@L).mean())])
def stats(data):
 a=np.array(data);w=a[:,0];w/=w.sum()
 def quant(col,q):
  order=np.argsort(a[:,col]);return float(np.interp(q,np.cumsum(w[order]),a[order,col]))
 return {'triangles':len(a),'density_px_m':float(w@a[:,1]),'density_p05_p95':[quant(1,.05),quant(1,.95)],'uv_anisotropy_p95':quant(2,.95),'srgb_luminance':float(w@a[:,3]),'linear_luminance':float(w@a[:,4])}
report={k:stats(v) for k,v in rows.items()};report['ratios']={k:report['sleeves'][k]/report['torso'][k] for k in ['density_px_m','srgb_luminance','linear_luminance']};report['sampling']='Area-weighted surface samples; blue cloth only (exclude baked white belt/rope and skin projection).';report['limits']={'density_ratio':[.85,1.15],'srgb_luminance_ratio':[.9,1.1],'linear_luminance_ratio':[.85,1.2],'sleeve_uv_anisotropy_p95':2.0};rr=report['ratios'];report['pass']=.85<rr['density_px_m']<1.15 and .9<rr['srgb_luminance']<1.1 and .85<rr['linear_luminance']<1.2 and report['sleeves']['uv_anisotropy_p95']<2
(p/'review/round3/cloth_metrics.json').write_text(json.dumps(report,indent=2));print('CLOTH',json.dumps(report));assert report['pass'],report
