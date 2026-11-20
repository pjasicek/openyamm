import bpy,numpy as np,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/skirt_rebuild_01');s=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2'];bpy.context.window.scene=s
D=np.load(ROOT/'radial_surface.npz');rdata=D['r'];zs=D['zs'];angles=D['angles'];specs=json.loads((ROOT/'construction_report.json').read_text())['panels'];fits=[]
for t in [0,.3,.6,.85,1.]:
 points=[]
 for sp in specs:
  i=sp['index'];a=((sp['left_column']+sp['right_column'])/2/720*2-1)*math.pi;z=sp['top']*(1-t)+(sp['tip']+.022)*t
  if i in [3,4,5] and t<.8:continue
  iz=int(np.argmin(abs(zs-z)));ia=int(np.argmin(abs(angles-a)));vals=rdata[max(0,iz-4):iz+5,max(0,ia-3):ia+4];vals=vals[np.isfinite(vals)]
  if len(vals)<5:continue
  rr=float(np.quantile(vals,.25));points.append((rr*math.sin(a),-rr*math.cos(a)))
 pts=np.array(points);x,y=pts.T;M=np.array([x*x,y*y,y]).T;coef=np.linalg.lstsq(M,np.ones(len(pts)),rcond=None)[0];fits.append(coef)
print('ellipse fits',np.array(fits).tolist())
def radius(a,t):
 levels=[0,.3,.6,.85,1.];k=min(3,max(0,np.searchsorted(levels,t)-1));f=(t-levels[k])/(levels[k+1]-levels[k]);A,B,C=fits[k]*(1-f)+fits[k+1]*f;ca=math.cos(a);sa=math.sin(a);dd=A*sa*sa+B*ca*ca;return (C*ca+math.sqrt((C*ca)**2+4*dd))/(2*dd)
low=next(o for o in s.objects if o.name.startswith('Goblin_SkirtBelt_Low'));proxy=next(o for o in s.objects if o.name.startswith('Skirt_BakeSurface'));cage=s.objects['Skirt_RadialBakeCage'];me=low.data
updates={}
def key(p):return tuple(round(float(c),6) for c in p)
for p in me.polygons:
 if p.material_index!=0:continue
 for li in p.loop_indices:
  uv=me.uv_layers.active.data[li].uv
  if uv.y>.78:continue
  tx=int(math.floor((uv.x-.022+1e-5)/.108));ty=int(math.floor((uv.y-.025+1e-5)/.38));i=ty*9+tx
  if not 0<=i<17:continue
  sp=specs[i];u=(uv.x-(.022+tx*.108))/.094;v=(uv.y-(.025+ty*.38))/.345;t=min(1,max(0,1-v));width=.86 if v>.999 else 1.
  mid=(sp['left_column']+sp['right_column'])/2;col=mid+(u-.5)*(sp['right_column']-sp['left_column'])*width;a=(col/720*2-1)*math.pi;z=sp['tip']+v*(sp['top']-sp['tip']);rr=radius(a,t)
  new=Vector((math.sin(a)*rr,-math.cos(a)*rr,z));old=me.vertices[me.loops[li].vertex_index].co.copy();updates[key(old)]=new
  d=Vector((old.x,old.y,0)).normalized();nd=Vector((new.x,new.y,0)).normalized();updates[key(old-d*.004)]=new-nd*.004
for m in [me,proxy.data]:
 for v in m.vertices:
  if key(v.co) in updates:v.co=updates[key(v.co)]
 m.update()
for v,pv in zip(cage.data.vertices,proxy.data.vertices):
 v.co=pv.co.copy();v.co+=Vector((v.co.x,v.co.y,0)).normalized()*.03
# Keep the belt's inner upper rim close to the body; outer UV-mapped surface is unchanged.
# This is a clothing fit study; leave the current thin thickness for export consistency.
(ROOT/'strip_surface_fit.json').write_text(json.dumps({'fit_parameters':[c.tolist() for c in fits],'method':'Smooth elliptical cross-sections fitted to source strip centers, excluding pouch, to avoid casting edge vertices into gaps.','updated_coordinate_keys':len(updates)},indent=2)+'\n')
mat=me.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');normal=next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP');img=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
high=next(o for o in s.objects if o.name.startswith('Skirt_DenseBakeSource'));high.hide_render=False;high.hide_set(False);proxy.hide_render=False;proxy.hide_set(False);bpy.ops.object.select_all(action='DESELECT');high.select_set(True);proxy.select_set(True);bpy.context.view_layer.objects.active=proxy
bpy.ops.object.bake(type='NORMAL');img.save();img.pack();high.hide_render=True;high.hide_set(True);proxy.hide_render=True;proxy.hide_set(True);mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
s.camera.data.ortho_scale=.82
for view,offset in [('front',(0,-4,0)),('quarter',(-3,-4,.5)),('back',(0,4,0))]:
 s.camera.location=offset;s.camera.rotation_euler=(-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/(view+'_baked.png'));bpy.ops.render.render(write_still=True)
print('Regularized panel surfaces and rebaked.')
