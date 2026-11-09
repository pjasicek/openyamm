"""Fit returned and painted Meshy props to canonical grip frames; retain source geometry and UVs."""
import bpy,bmesh,math,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipment.blend'))
for name in ['pulse_pistol','collar_rod','arc_maul']:
 o=bpy.data.objects.get('OV_'+name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
report={}
for name,outname,length in [('pulse_pistol','pulse_pistol',.46),('collar_staff','collar_rod',1.25),('arc_maul','arc_maul',1.16)]:
 with bpy.data.libraries.load(str(P/'work/weapons'/f'{name}_painted.blend'),link=False) as (src,dst):dst.objects=[name]
 o=dst.objects[0];bpy.context.scene.collection.objects.link(o);o.name=o.data.name='OV_'+outname
 co=np.array([v.co[:] for v in o.data.vertices]);lo=co.min(0);hi=co.max(0)
 if name=='pulse_pistol':
  # The generated sidearm points -X. Its grip centre is measured from the lower rear handle.
  centre=np.array([.31,0,.185]);R=Matrix.Rotation(math.pi/2,3,'Z');scale=length/(hi[0]-lo[0])
 else:
  # Fit the shaft through its middle third; remove the presentation lean without bending the mesh.
  shaft=co[(co[:,2]>.25)&(co[:,2]<.65)];slope=np.polyfit(shaft[:,2],shaft[:,0],1)[0]
  R=Matrix.Rotation(-math.atan(slope),3,'Y');rotated=co@np.array(R).T
  scale=length/(rotated[:,2].max()-rotated[:,2].min())
  z=.53 if name=='collar_staff' else .43
  centre=np.array([np.polyval(np.polyfit(shaft[:,2],shaft[:,0],1),z),float(np.median(shaft[:,1])),z])
 transformed=(co-centre)@np.array(R).T*scale
 # Fit the existing leather handle to the retained large claws, tapering into the original shaft.
 if name!='pulse_pistol':
  # Keep the generated head and shaft; fit the existing handle to one common cylindrical grasp.
  z=transformed[:,2];grid=np.linspace(-.30,.30,31);centres=[];edges=np.array([e.vertices[:] for e in o.data.edges]);aa=transformed[edges[:,0]];bb=transformed[edges[:,1]]
  for zz in grid:
   cross=(aa[:,2]-zz)*(bb[:,2]-zz)<0;lo,hi=aa[cross],bb[cross];part=lo[:,:2]+(hi-lo)[:,:2]*((zz-lo[:,2])/(hi[:,2]-lo[:,2]))[:,None];assert len(part)>2;centres.append((part.min(0)+part.max(0))/2)
  centres=np.array(centres);centreline=np.column_stack([np.interp(z,grid,centres[:,axis]) for axis in range(2)]);radial=transformed[:,:2]-centreline;lengths=np.maximum(np.linalg.norm(radial,axis=1),1e-6);fitted=radial*(.032/lengths[:,None]);strength=np.clip((.24-np.abs(z))/.07,0,1);strength=strength*strength*(3-2*strength);transformed[:,:2]=transformed[:,:2]*(1-strength[:,None])+fitted*strength[:,None]
 else:
  strength=np.clip((.13-np.abs(transformed[:,2]))/.06,0,1)*np.clip((transformed[:,1]+.065)/.03,0,1);transformed[:,0]*=1+.3*strength
 for v,x in zip(o.data.vertices,transformed):v.co=x
 if name=='arc_maul':
  # Refine coarse circumference chords before projection so the fitted handle stays round between vertices.
  bm=bmesh.new();bm.from_mesh(o.data);chosen=[]
  for edge in bm.edges:
   a,b=[v.co for v in edge.verts]
   if max(abs(a.z),abs(b.z))>.18:continue
   aa=Vector((a.x,a.y));bb=Vector((b.x,b.y))
   if aa.length>.02 and bb.length>.02 and aa.angle(bb)>math.radians(22):chosen.append(edge)
  bmesh.ops.subdivide_edges(bm,edges=chosen,cuts=1,use_grid_fill=True)
  for v in bm.verts:
   if abs(v.co.z)<.17:
    r=math.hypot(v.co.x,v.co.y)
    if r>1e-6:v.co.x*=.032/r;v.co.y*=.032/r
  bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.to_mesh(o.data);bm.free();transformed=np.array([v.co[:] for v in o.data.vertices])
 # Align the modeled striking face with the measured downstroke; preserve the fitted grip itself.
 roll=math.radians({'pulse_pistol':0,'collar_staff':72.55745908,'arc_maul':-17.88557811}[name])
 strength=np.clip((np.abs(transformed[:,2])-.17)/.07,0,1);strength=strength*strength*(3-2*strength)
 theta=roll*strength;x=transformed[:,0].copy();y=transformed[:,1].copy();transformed[:,0]=x*np.cos(theta)-y*np.sin(theta);transformed[:,1]=x*np.sin(theta)+y*np.cos(theta)
 for v,x in zip(o.data.vertices,transformed):v.co=x
 o.matrix_world=Matrix.Identity(4);base=o.data.materials[0];base.use_backface_culling=True
 grip=base.copy();grip.name='OV_Grip_'+name;grip.use_backface_culling=True;o.data.materials.append(grip)
 glow=bpy.data.materials.new('OV_Glow_'+name);glow.use_nodes=True;glow.use_backface_culling=True;bs=glow.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(1,.35,.025,1);bs.inputs['Emission Color'].default_value=(1,.35,.025,1);bs.inputs['Emission Strength'].default_value=1;o.data.materials.append(glow)
 for f in o.data.polygons:
  pts=transformed[list(f.vertices)];z=pts[:,2].mean();x,y=pts[:,:2].mean(0);cell_x=x*math.cos(roll)+y*math.sin(roll)
  is_grip=(abs(z)<.085 and y>-.045) if name=='pulse_pistol' else abs(z)<.13
  f.material_index=1 if is_grip else 0
  # Separate only the central modeled cell; retain brass highlights in the painted material.
  cell=(.09<z<.18 and -.29<y<-.085 and np.max(np.abs(pts[:,0]))<.01) if name=='pulse_pistol' else (.47<z<.58 and abs(cell_x)<.020) if name=='collar_staff' else (.48<z<.61 and abs(cell_x)<.042)
  if cell and not is_grip:f.material_index=2
 for material in [base,grip]:
  for node in material.node_tree.nodes:
   if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.18
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
 report[outname]={'source':f'work/weapons/{name}_painted.blend','head_roll_deg':math.degrees(roll),'scale':float(scale),'source_grip_centre':centre.tolist(),'rotation':list(map(list,R)),'bounds':[transformed.min(0).tolist(),transformed.max(0).tolist()],'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'grip_faces':sum(f.material_index==1 for f in o.data.polygons),'glow_faces':sum(f.material_index==2 for f in o.data.polygons)}
 assert report[outname]['grip_faces']>0
 # Host grip solver uses these exact surfaces; canonical +Z is the grip axis, -Y the pistol muzzle.
 np.savez(P/'work/weapons'/f'{outname}_grip_mesh.npz',vertices=transformed,faces=np.array([f.vertices[:] for f in o.data.polygons]),grip=np.array([f.material_index==1 for f in o.data.polygons]))
print('WEAPON_FITS',report,flush=True)
(P/'work/weapons/fit.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipment_meshy.blend'))
